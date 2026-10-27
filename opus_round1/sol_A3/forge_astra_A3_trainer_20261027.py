#!/usr/bin/env python3
"""Forge full-NNUE trainer (Astra A3, 2026-10-27). Offline / CPU pipeline; no engine integration.

Network "FN1" (spec: forge_astra_A3_fullnnue_spec_20261027.md):
  inputs   768 x KB king-bucketed piece-square features per perspective (A2 layout M4 by default: mirrored,
           4 blocks, C4 standard half-board map), kings included as features;
  FT       768*KB -> H per perspective, int16-quantised weights/bias (x 4096, QAT), so the engine's float32
           accumulator is exact; activation SCReLU = clamp(x, 0, 1)^2;
  stack    per output bucket (8 by piece count): [SCReLU(stm acc), SCReLU(other acc)] (2H) -> L1 -> CReLU
           -> L2 -> CReLU -> 1 (L2 = 0: one hidden layer, 2H -> L1 -> CReLU -> 1); float32 weights;
  output   in sigmoid units of K/400 per centipawn (K = 2.25): cp = out * 400 / K. Stand-alone (no HCE).

Data and loader conventions follow train_resid_v3b.py (LA/5_nnue/trainers, read only): FPOS v1 .pos files
(16-byte header, n x 32 nibble boards a1..h8, n x int16 STM score, n x u8 meta: bit0 black to move, bits1-2
WHITE result*2), optional FHCE .hce files (used only for the HCE-alone baseline line), holdout = whole files,
loss = MSE(sigmoid(out), blend * sigmoid(K*score/400) + (1 - blend) * stm_result) with a linear blend ramp,
lr warmup + cosine to --min-lr-frac, validation subset drawn with numpy default_rng(12345), shuffles with
default_rng(seed * 1000 + epoch). Differences from v3b: synchronous batches (no prefetch thread), stock Adam,
deterministic CPU mode (torch.set_num_threads(--threads), torch.use_deterministic_algorithms(True)).

Each epoch writes <run>/epochNNN-stepXXXXXXXXX.pt (config + model state + optimizer state) and .json (metrics).
Convert a checkpoint to the engine file with forge_astra_A3_converter_20261027.py. Never run this file under a
name starting with train_resid (PC supervisor rule); run a copy named opus_nnue_smoke_<name>.py.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time
import uuid
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

FEATURES = 768
SCALE = 4096.0
K_DEFAULT = 2.25
QMAX = 32767

# Half-board king layouts (files a-d, rank 1 first, perspective's own side; files e-h mirror onto d-a).
# Same rows as C4's tools/nnue/forge_nnue_v2.py standard layouts (A2 recommends M4).
HALF_ROWS = {
    1: ["0000"] * 8,
    2: ["0000", "0000"] + ["1111"] * 6,
    4: ["0011", "0011", "2222", "2222"] + ["3333"] * 4,
    8: ["0123", "4455", "6666"] + ["7777"] * 5,
    16: ["0123", "4567", "8899", "aabb", "cccc", "dddd", "eeee", "ffff"],
}


def half_layout(n: int) -> list[int]:
    if n == 32:
        return list(range(32))
    if n not in HALF_ROWS:
        raise ValueError(f"no standard half-board layout for {n} king buckets (1, 2, 4, 8, 16, 32)")
    return [int(ch, 16) for row in HALF_ROWS[n] for ch in row]


def king_map_from(n: int, mirror: bool) -> list[int]:
    """64-entry map own-king square (perspective frame) -> weight block."""
    half = half_layout(n)
    out = []
    for sq in range(64):
        f, r = sq & 7, sq >> 3
        b = half[r * 4 + (f if f < 4 else 7 - f)]
        out.append(b if mirror else b + (n if f >= 4 else 0))
    return out


def output_map_default(n: int) -> list[int]:
    """33 entries, piece count (kings included) 0..32 -> output bucket; for 8: (pieces - 2) // 4 (C5's map)."""
    return [min(n - 1, max(0, p - 2) * n // 32) for p in range(33)]


# ----------------------------------------------------------------------------- data (v3b conventions)
def read_pos_header(path):
    with open(path, "rb") as f:
        h = f.read(16)
    if h[:4] != b"FPOS" or int.from_bytes(h[4:8], "little") != 1:
        raise ValueError(f"bad pos header {path}")
    return int.from_bytes(h[8:16], "little")


def load_set(pos_files, hce_dir=None, limit=None):
    """v3b load_set: pos (+ hce when hce_dir) files into RAM in the given order; limit takes file prefixes."""
    picks, total = [], 0
    for p in pos_files:
        n = read_pos_header(p)
        n_use = limit - total if limit is not None and total + n > limit else n
        if n_use <= 0:
            break
        picks.append((p, n, n_use))
        total += n_use
    boards = np.empty((total, 32), np.uint8)
    score = np.empty(total, np.int16)
    meta = np.empty(total, np.uint8)
    hce = np.zeros(total, np.int16)
    o = 0
    for p, n, n_use in picks:
        b = np.memmap(p, np.uint8, "r", 16, (n, 32))
        s = np.memmap(p, np.int16, "r", 16 + n * 32, (n,))
        m = np.memmap(p, np.uint8, "r", 16 + n * 34, (n,))
        boards[o:o + n_use] = b[:n_use]
        score[o:o + n_use] = s[:n_use]
        meta[o:o + n_use] = m[:n_use]
        if (m[:n_use] == 255).any():
            raise ValueError(f"bad records in {p}")
        if hce_dir:
            hp = Path(hce_dir) / (Path(p).stem + ".hce")
            with open(hp, "rb") as f:
                h = f.read(16)
            if h[:4] != b"FHCE" or int.from_bytes(h[8:16], "little") != n:
                raise ValueError(f"hce header/count mismatch {hp} vs {p}")
            hh = np.memmap(hp, np.int16, "r", 16, (n,))
            if (hh[:n_use] == -32768).any():
                raise ValueError(f"bad hce in {hp}")
            hce[o:o + n_use] = hh[:n_use]
            del hh
        del b, s, m
        o += n_use
    return dict(boards=boards, score=score, meta=meta, hce=hce, n=total, files=[(p, nu) for p, _, nu in picks])


def make_batch(d, idx):
    """v3b make_batch: nibble boards -> codes [B,64] (0 empty, 1..6 white PNBRQK, 7..12 black)."""
    b = d["boards"][idx]
    codes = np.empty((len(idx), 64), np.uint8)
    codes[:, 0::2] = b & 15
    codes[:, 1::2] = b >> 4
    m = d["meta"][idx]
    return codes, (m & 1), (m >> 1), d["score"][idx], d["hce"][idx]


def to_tensors(bt):
    codes, stm, wres, score, hce = bt
    return (torch.from_numpy(codes.astype(np.int64)), torch.from_numpy(stm.astype(np.int64)),
            torch.from_numpy(wres.astype(np.float32)), torch.from_numpy(score.astype(np.float32)),
            torch.from_numpy(hce.astype(np.float32)))


def targets(score_t, stm_t, wres_t, k, blend):
    """v3b targets(): teacher = sigmoid(K*score/400), stm result, blended target."""
    teacher = torch.sigmoid(torch.clamp(score_t * (k / 400.0), -40, 40))
    white = wres_t * 0.5
    stm_res = torch.where(stm_t == 0, white, 1.0 - white)
    return teacher, stm_res, blend * teacher + (1.0 - blend) * stm_res


# ----------------------------------------------------------------------------- features
def king_features(codes, black, king_map, mirror, kb):
    """codes [B,64] int64, black [B] int64 (perspective colour) -> feature indices [B,64] in [0, kb*768],
    kb*768 = empty square. Own king = first own king on a1..h8 (square 0 if a malformed record has none), as C4."""
    sq = torch.arange(64).unsqueeze(0)
    c = codes - 1
    color = torch.div(c, 6, rounding_mode="floor")
    typ = c - color * 6
    bl = black.unsqueeze(1)
    rel = (color != bl).long()
    rsq = torch.where(bl == 1, sq ^ 56, sq.expand_as(codes))
    own_king = torch.where(black == 1, 12, 6).unsqueeze(1)
    ksq = torch.argmax((codes == own_king).long(), dim=1)
    kr = torch.where(black == 1, ksq ^ 56, ksq)
    flip = torch.where((kr & 7) >= 4, 7, 0) if mirror else torch.zeros_like(kr)
    block = king_map[kr]
    f = block.unsqueeze(1) * FEATURES + (rel * 6 + typ) * 64 + (rsq ^ flip.unsqueeze(1))
    return torch.where(codes > 0, f, torch.full_like(f, kb * FEATURES))


def dense_input(codes, black, king_map, mirror, kb):
    f = king_features(codes, black, king_map, mirror, kb)
    x = torch.zeros(codes.shape[0], kb * FEATURES + 1).scatter_(1, f, 1.0)
    return x[:, :kb * FEATURES]


def quantise(p):
    """v3b q(): round half away from zero to the 1/4096 grid, clamp to int16; straight-through gradient.
    The forward value equals the grid value exactly in float32 (qv - p is exact by Sterbenz's lemma)."""
    scaled = p * SCALE
    rounded = torch.sign(scaled) * torch.floor(torch.abs(scaled) + 0.5)
    qv = torch.clamp(rounded, -QMAX, QMAX) / SCALE
    return p + (qv - p).detach()


class FullNNUE(nn.Module):
    def __init__(self, hidden, l1, l2, king_map, mirror, factor, output_map, qat=True):
        super().__init__()
        self.hidden, self.l1, self.l2, self.mirror, self.qat = hidden, l1, l2, bool(mirror), qat
        self.register_buffer("king_map", torch.tensor(king_map, dtype=torch.long))
        self.register_buffer("output_map", torch.tensor(output_map, dtype=torch.long))
        self.kb = max(king_map) + 1
        self.ob = max(output_map) + 1
        self.ft_w = nn.Parameter(torch.zeros(self.kb, hidden, FEATURES))
        self.ft_f = nn.Parameter(torch.zeros(hidden, FEATURES)) if factor else None
        self.ft_b = nn.Parameter(torch.zeros(hidden))
        nn.init.normal_(self.ft_f if factor else self.ft_w, std=0.02)
        self.fc1 = nn.Linear(2 * hidden, self.ob * l1)
        if l2:
            self.fc2 = nn.Linear(l1, self.ob * l2)
            self.out = nn.Linear(l2, self.ob)
        else:
            self.fc2 = None
            self.out = nn.Linear(l1, self.ob)

    def ft_folded(self):
        """[KB, H, 768] block weights incl. the factoriser (before quantisation)."""
        return self.ft_w if self.ft_f is None else self.ft_w + self.ft_f.unsqueeze(0)

    def ft_params(self):
        w = self.ft_folded()
        if self.qat:
            return quantise(w), quantise(self.ft_b)
        return w, self.ft_b

    def accumulators(self, codes, stm):
        """Pre-activation accumulators (stm, other) [B, H] each; exact grid sums with QAT."""
        w, b = self.ft_params()
        w = w.permute(1, 0, 2).reshape(self.hidden, self.kb * FEATURES)
        a_s = F.linear(dense_input(codes, stm, self.king_map, self.mirror, self.kb), w, b)
        a_o = F.linear(dense_input(codes, 1 - stm, self.king_map, self.mirror, self.kb), w, b)
        return a_s, a_o

    def bucket(self, codes):
        pieces = (codes > 0).sum(1).clamp(max=32)
        return self.output_map[pieces]

    def forward(self, codes, stm):
        a_s, a_o = self.accumulators(codes, stm)
        x = torch.cat([torch.clamp(a_s, 0.0, 1.0).square(), torch.clamp(a_o, 0.0, 1.0).square()], 1)
        ob = self.bucket(codes)
        rows = torch.arange(codes.shape[0])
        h = self.fc1(x).view(-1, self.ob, self.l1)[rows, ob]
        h = torch.clamp(h, 0.0, 1.0)
        if self.fc2 is not None:
            h = self.fc2(h).view(-1, self.ob, self.l2)[rows, ob]
            h = torch.clamp(h, 0.0, 1.0)
        return self.out(h)[rows, ob]

    @torch.no_grad()
    def project_weights(self):
        """Keep the quantised feature-transform parameters inside int16 (v3b project_weights, FT only)."""
        lim = QMAX / SCALE
        self.ft_b.clamp_(-lim, lim)
        if self.ft_f is None:
            self.ft_w.clamp_(-lim, lim)


def config_of(model, a=None):
    cfg = {"format": "FN1", "features": "forge768-king-buckets", "hidden": model.hidden, "l1": model.l1,
           "l2": model.l2, "king_blocks": model.kb, "king_mirror": model.mirror,
           "king_map": model.king_map.tolist(), "output_buckets": model.ob, "output_map": model.output_map.tolist(),
           "factor": model.ft_f is not None, "qat": model.qat, "sigmoid_k": K_DEFAULT,
           "ft_activation": "screlu", "hidden_activation": "crelu"}
    if a is not None:
        cfg.update({"epochs": a.epochs, "batch_size": a.batch_size, "lr": a.lr, "seed": a.seed})
    return cfg


def build_model(cfg):
    """Rebuild a FullNNUE from a checkpoint config (used by the converter and the parity test)."""
    return FullNNUE(cfg["hidden"], cfg["l1"], cfg["l2"], cfg["king_map"], cfg["king_mirror"], cfg["factor"],
                    cfg["output_map"], qat=cfg["qat"])


# ----------------------------------------------------------------------------- training
@torch.no_grad()
def evaluate(model, d, idx_all, k, batch, blends=(1.0, 0.6, 0.8), baseline=False):
    sums = {b: 0.0 for b in blends}
    cnt = 0
    model.eval()
    for i in range(0, len(idx_all) - batch + 1, batch):
        codes, stm, wres, score, hce = to_tensors(make_batch(d, idx_all[i:i + batch]))
        logit = hce * (k / 400.0) if baseline else model(codes, stm)
        pred = torch.sigmoid(logit)
        for b in blends:
            _, _, tg = targets(score, stm, wres, k, b)
            sums[b] += float(F.mse_loss(pred, tg, reduction="sum"))
        cnt += len(codes)
    model.train()
    return {b: sums[b] / max(cnt, 1) for b in blends}, cnt


def atomic_write(path: Path, write):
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    with open(temp, "xb") as dst:
        write(dst)
        dst.flush()
        os.fsync(dst.fileno())
    if path.exists():
        raise FileExistsError(str(path))
    os.rename(temp, path)


def expand(patterns):
    out = []
    for p in patterns:
        out.extend(sorted(glob.glob(p)))
    return sorted(set(out))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", nargs="+", required=True)
    ap.add_argument("--holdout", nargs="+", required=True)
    ap.add_argument("--hce-dir", help="optional: <stem>.hce files, only for the HCE-alone baseline line")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--king-buckets", type=int, default=4, help="standard layout 1/2/4/8/16/32 (A2: 4)")
    ap.add_argument("--king-mirror", type=int, choices=[0, 1], default=1)
    ap.add_argument("--king-factor", type=int, choices=[0, 1], default=1)
    ap.add_argument("--hidden", type=int, default=256, help="feature transformer width H (multiple of 16)")
    ap.add_argument("--l1", type=int, default=16, help="first hidden layer width (multiple of 16)")
    ap.add_argument("--l2", type=int, default=32, help="second hidden layer width (multiple of 16; 0 = one hidden layer)")
    ap.add_argument("--output-buckets", type=int, default=8)
    ap.add_argument("--no-qat", action="store_true")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch-size", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--min-lr-frac", type=float, default=0.01)
    ap.add_argument("--warmup-steps", type=int, default=20)
    ap.add_argument("--blend-start", type=float, default=1.0)
    ap.add_argument("--blend-end", type=float, default=0.6)
    ap.add_argument("--sigmoid-k", type=float, default=K_DEFAULT)
    ap.add_argument("--max-train", type=int, default=0)
    ap.add_argument("--val-positions", type=int, default=16384)
    ap.add_argument("--steps-per-epoch", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--log-every", type=int, default=50, help="log every N steps")
    a = ap.parse_args(argv)
    for name, v in (("--hidden", a.hidden), ("--l1", a.l1), ("--l2", a.l2)):
        if v % 16 or (v == 0 and name != "--l2"):
            raise SystemExit(f"{name} must be a positive multiple of 16 (the engine's 16-lane order)")
    run = Path(a.run_dir)
    if run.name.startswith(("runs_", "smoke_kb")) or "train_resid" in Path(sys.argv[0]).name:
        raise SystemExit("refusing: run folder names runs_*/smoke_kb* and train_resid* script names are reserved")
    if a.sigmoid_k != K_DEFAULT:
        raise SystemExit("the format fixes sigmoid K = 2.25")
    torch.set_num_threads(a.threads)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(a.seed)
    if run.exists():
        raise SystemExit(f"run folder {run} exists; give a new one")
    k = a.sigmoid_k
    kmap = king_map_from(a.king_buckets, bool(a.king_mirror))
    omap = output_map_default(a.output_buckets)
    model = FullNNUE(a.hidden, a.l1, a.l2, kmap, a.king_mirror, a.king_factor, omap, qat=not a.no_qat)
    cfg = config_of(model, a)
    print(f"FN1 trainer: KB {model.kb} mirror {model.mirror} factor {a.king_factor} H {a.hidden} L1 {a.l1} "
          f"L2 {a.l2} OB {model.ob} qat {not a.no_qat} seed {a.seed} threads {a.threads} torch {torch.__version__}",
          flush=True)
    t0 = time.time()
    hold_files = expand(a.holdout)
    hold = load_set(hold_files, a.hce_dir)
    print(f"holdout: {hold['n']:,} positions from {len(hold_files)} files", flush=True)
    rng = np.random.default_rng(12345)
    if a.val_positions and a.val_positions < hold["n"]:
        val_idx = np.sort(rng.choice(hold["n"], a.val_positions, replace=False))
    else:
        val_idx = np.arange(hold["n"], dtype=np.int64)
    if a.hce_dir:
        base, nb = evaluate(model, hold, val_idx, k, a.batch_size, baseline=True)
        print(f"BASELINE HCE-alone holdout subset n={nb:,}: mse_teacher={base[1.0]:.6f} mse_b0.6={base[0.6]:.6f}", flush=True)
    if not hold_files or hold["n"] < a.batch_size:
        raise SystemExit(f"holdout {a.holdout} matched {len(hold_files)} files / {hold['n']} positions (< one batch)")
    train_files = [f for f in expand(a.train) if f not in hold_files]
    if not train_files:
        raise SystemExit(f"--train {a.train} matched no files (outside the holdout)")
    train = load_set(train_files, None, limit=a.max_train or None)
    N = train["n"]
    print(f"train: {N:,} positions from {len(train['files'])} files ({time.time() - t0:.1f}s load): "
          + ", ".join(f"{Path(p).name} {n:,}" for p, n in train["files"]), flush=True)
    spe = N // a.batch_size
    if a.steps_per_epoch:
        spe = min(spe, a.steps_per_epoch)
    total_steps = spe * a.epochs
    if total_steps < 1:
        raise SystemExit(f"{N} training positions give no full batch of {a.batch_size}")
    run.mkdir(parents=True, exist_ok=False)
    (run / "settings.json").write_text(json.dumps({"argv": sys.argv[1:], "args": vars(a), "config": cfg}, indent=1))
    opt = torch.optim.Adam(model.parameters(), lr=a.lr, foreach=False)

    def lr_at(s):
        if s < a.warmup_steps:
            return a.lr * (s + 1) / a.warmup_steps
        pr = (s - a.warmup_steps) / max(1, total_steps - a.warmup_steps)
        return a.lr * (a.min_lr_frac + (1 - a.min_lr_frac) * 0.5 * (1 + math.cos(math.pi * min(pr, 1.0))))

    def blend_at(s):
        return a.blend_start + (a.blend_end - a.blend_start) * min(1.0, s / max(1, total_steps - 1))

    print(f"steps/epoch={spe:,} total={total_steps:,} batch={a.batch_size} lr={a.lr} blend {a.blend_start}->{a.blend_end}", flush=True)
    step = 0
    for ep in range(a.epochs):
        order = np.arange(N, dtype=np.int64)
        np.random.default_rng(a.seed * 1000 + ep).shuffle(order)
        te, ep_loss, ep_n = time.time(), 0.0, 0
        for i in range(spe):
            idx = np.sort(order[i * a.batch_size:(i + 1) * a.batch_size])
            codes, stm, wres, score, _ = to_tensors(make_batch(train, idx))
            for g in opt.param_groups:
                g["lr"] = lr_at(step)
            blend = blend_at(step)
            _, _, tg = targets(score, stm, wres, k, blend)
            opt.zero_grad(set_to_none=True)
            loss = F.mse_loss(torch.sigmoid(model(codes, stm)), tg)
            loss.backward()
            opt.step()
            model.project_weights()
            v = float(loss)
            if not math.isfinite(v):
                raise RuntimeError("non-finite loss")
            ep_loss += v * len(idx)
            ep_n += len(idx)
            step += 1
            if step % a.log_every == 0:
                print(f"ep{ep + 1} step {step:,}/{total_steps:,} blend={blend:.3f} lr={lr_at(step):.2e} "
                      f"train_mse={ep_loss / ep_n:.6f}", flush=True)
        vs, nv = evaluate(model, hold, val_idx, k, a.batch_size)
        print(f"EPOCH {ep + 1}/{a.epochs} done in {time.time() - te:.1f}s train_mse={ep_loss / max(ep_n, 1):.6f} | HOLDOUT "
              f"n={nv:,} mse_teacher={vs[1.0]:.6f} mse_b0.6={vs[0.6]:.6f} mse_b0.8={vs[0.8]:.6f}", flush=True)
        stem = run / f"epoch{ep + 1:03d}-step{step:09d}"
        payload = {"config": cfg, "model": {n: t.detach().clone() for n, t in model.state_dict().items()},
                   "optimizer": opt.state_dict(), "next_epoch": ep + 1, "step": step,
                   "val": {str(b): v for b, v in vs.items()}}
        atomic_write(stem.with_suffix(".pt"), lambda dst: torch.save(payload, dst))
        metrics = {"epoch": ep + 1, "step": step, "train_mse": ep_loss / max(ep_n, 1), "val": payload["val"], "n_val": nv}
        atomic_write(stem.with_suffix(".json"), lambda dst: dst.write((json.dumps(metrics, indent=1) + "\n").encode()))
        print(f"Saved {stem.name} (.pt .json)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
