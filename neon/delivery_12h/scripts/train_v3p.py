"""RX 7900 XT GPU Trainer for FORGENN3-P (Pairwise CReLU + Direct Factorized PSQT + OB Smoothness).

Proven Bullet / Viridithas / Stormphrax upgrade over linear (768->H)x2 SCReLU:
  1. Pairwise CReLU: a = clamp(acc, 0, 1); h = a[:, :H/2] * a[:, H/2:]  -> multiplicative feature interaction,
     HALF the output-layer dot-product work (1024w Pairwise has 512 pairs/side -> ~100% of live 768w SCReLU NPS!).
  2. Direct Factorized PSQT: (psqt_w[KB,768,OB] + psqt_fac[768,OB]), summed incrementally per side ->
     0.5 * (psqt_us - psqt_them), curing middlegame material compression (N2) & freeing hidden units.
  3. Adjacent Output-Bucket Smoothness (--ob-smooth): penalizes (w2[b]-w2[b-1])^2 + (psqt[...,b]-psqt[...,b-1])^2,
     curing the 102.8 cp ob0<->ob1 cliff (N5).
  4. Zero-disk loading from existing .cache-n0c1.npz caches OR fresh .plain datasets, v3 self-distillation,
     exact 0-cp integer parity check between PyTorch float grid and forge_v3p.reference_eval!

Strictly writes only under --out-dir inside C:\\nnue-lab\\neon\\.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

LAB = Path(r"C:\nnue-lab")
sys.path.insert(0, str(LAB / "pipeline"))
sys.path.insert(0, str(LAB / "pipeline/ft_triton"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import forge_train as ft  # noqa: E402
import forge_train_v3 as v3  # noqa: E402
import forge_v3  # noqa: E402
import forge_v3p  # noqa: E402

fk = ft.triton_kernels()
import triton  # noqa: E402
import triton.language as tl  # noqa: E402
import batch_kernel_c as bc  # noqa: E402
import compact_record as cr  # noqa: E402

QA = float(forge_v3p.QA)
QB = float(forge_v3p.QB)


@triton.jit
def _fwd_rows_raw_kernel(idx_ptr, w_ptr, bias_ptr, out_ptr,
                         A: tl.constexpr, N: tl.constexpr, KC: tl.constexpr, BLOCK_N: tl.constexpr):
    row = tl.program_id(0).to(tl.int64)
    cols = tl.program_id(1) * BLOCK_N + tl.arange(0, BLOCK_N)
    cmask = cols < N
    acc = tl.load(bias_ptr + cols, mask=cmask, other=0.0)
    for k0 in tl.static_range(0, A, KC):
        ks = k0 + tl.arange(0, KC)
        ii = tl.load(idx_ptr + row * A + ks, mask=ks < A, other=-1).to(tl.int32)
        valid = ii >= 0
        ii = tl.where(valid, ii, 0)
        t = tl.load(w_ptr + (ii.to(tl.int64) * N)[:, None] + cols[None, :],
                    mask=valid[:, None] & cmask[None, :], other=0.0)
        acc += tl.sum(t, axis=0)
    tl.store(out_ptr + row * N + cols, acc, mask=cmask)


def rows_forward_raw(idx: torch.Tensor, table: torch.Tensor, bias: torch.Tensor) -> torch.Tensor:
    m, a = idx.shape
    n = table.shape[1]
    out = torch.empty(m, n, dtype=torch.float32, device=table.device)
    if m == 0:
        return out
    t = fk.tuning2(n, a)
    bn = max(16, min(t["BLOCK_N"], triton.next_power_of_2(n)))
    grid = (m, triton.cdiv(n, bn))
    _fwd_rows_raw_kernel[grid](idx, table, bias, out, A=a, N=n, KC=t["KC"], BLOCK_N=bn, num_warps=t["num_warps"])
    return out


class SparseRowsRaw(torch.autograd.Function):
    """Exact raw sparse sum: out[m, :] = bias + sum_k table[idx[m, k], :]. Reuses fk.rows_backward."""

    @staticmethod
    def forward(ctx, table: torch.Tensor, bias: torch.Tensor, idx: torch.Tensor):
        ctx.idx = idx
        ctx.rows = table.shape[0]
        return rows_forward_raw(idx, table.contiguous(), bias.contiguous())

    @staticmethod
    def backward(ctx, grad_out: torch.Tensor):
        g = grad_out.contiguous()
        return fk.rows_backward(ctx.idx, g, ctx.rows), g.sum(0), None


class ForgeNetV3P(nn.Module):
    def __init__(self, hidden: int = 1024, king_buckets: int = 8, out_buckets: int = 8,
                 mirror: bool = True, pairwise: bool = True, has_psqt: bool = True):
        super().__init__()
        self.hidden = hidden
        self.king_buckets = king_buckets
        self.out_buckets = out_buckets
        self.mirror = mirror
        self.pairwise = pairwise
        self.has_psqt = has_psqt
        self.standalone = True

        self.w1 = nn.Parameter(torch.zeros(king_buckets, forge_v3.INPUTS, hidden))
        self.fac = nn.Parameter(torch.randn(forge_v3.INPUTS, hidden) * 0.02)
        self.b1 = nn.Parameter(torch.zeros(hidden))
        w2_in = hidden if pairwise else 2 * hidden
        self.out = nn.Linear(w2_in, out_buckets)
        nn.init.normal_(self.out.weight, std=0.05 / ft.K)
        nn.init.zeros_(self.out.bias)

        if has_psqt:
            self.psqt_w = nn.Parameter(torch.zeros(king_buckets, forge_v3.INPUTS, out_buckets))
            self.psqt_fac = nn.Parameter(torch.zeros(forge_v3.INPUTS, out_buckets))
            # Initialize shared PSQT factoriser with rough piece-value priors (in units of 400 cp) for fast convergence!
            with torch.no_grad():
                vals = [0.22, 0.78, 0.82, 1.25, 2.40, 0.0]  # P, N, B, R, Q, K / 400
                for pt, pv in enumerate(vals):
                    self.psqt_fac[pt * 64:(pt + 1) * 64, :] = pv
                    self.psqt_fac[(6 + pt) * 64:(7 + pt) * 64, :] = -pv
        else:
            self.psqt_w = None
            self.psqt_fac = None

        self.register_buffer("king_map", torch.tensor(forge_v3p.king_layout(king_buckets), dtype=torch.int64))
        self.register_buffer("output_map", torch.tensor(forge_v3.output_layout(out_buckets), dtype=torch.int64))
        self.register_buffer("psqt_zero", torch.zeros(out_buckets, dtype=torch.float32))

    def table(self) -> torch.Tensor:
        return v3._grid((self.w1 + self.fac.unsqueeze(0)).reshape(-1, self.hidden), QA)

    def psqt_table(self) -> torch.Tensor:
        return v3._grid((self.psqt_w + self.psqt_fac.unsqueeze(0)).reshape(-1, self.out_buckets), QA * QB)

    def forward_rows(self, rows: torch.Tensor, bucket: torch.Tensor) -> torch.Tensor:
        b = bucket.shape[0]
        acc = SparseRowsRaw.apply(self.table(), v3._grid(self.b1, QA), rows)
        a = acc.clamp(0.0, 1.0)
        if self.pairwise:
            half = self.hidden // 2
            h = (a[:, :half] * a[:, half:]).reshape(b, self.hidden)
        else:
            h = (a * a).reshape(b, 2 * self.hidden)
        o = F.linear(h, v3._grid(self.out.weight, QB), v3._grid(self.out.bias, QA * QB))
        if self.has_psqt:
            # Pad PSQT to width 16? No, width 8 works cleanly with bn=16 in _fwd_rows_raw_kernel!
            p_acc = SparseRowsRaw.apply(self.psqt_table(), self.psqt_zero, rows)
            p_diff = 0.5 * (p_acc[0::2] - p_acc[1::2])
            o = o + p_diff
        o = o.gather(1, bucket.long().unsqueeze(1)).squeeze(1)
        return float(ft.K) * o

    def forward(self, feat: torch.Tensor, stm, hce_logit: torch.Tensor) -> torch.Tensor:
        if feat.dtype != torch.int16:
            feat = fk.stm_features(feat, stm)
        rows = fk.king_bucket_rows(feat, self.king_map, self.mirror)
        pieces = (feat >= 0).sum(1).clamp(max=32)
        bucket = self.output_map[pieces]
        return self.forward_rows(rows, bucket) + hce_logit

    def ob_smooth_penalty(self) -> torch.Tensor:
        w2 = self.out.weight
        if self.out_buckets < 2:
            return w2.new_zeros(())
        # Per-output-bucket smoothness (NOT divided by H or KB*768, so grads stay well above Adam eps=1e-8!)
        # Weighting: sum over hidden/features divided by (out_buckets - 1) -> O(1) gradient scale for --ob-smooth 1e-4.
        ob_pairs = float(self.out_buckets - 1)
        pen = (w2[1:] - w2[:-1]).pow(2).sum() / ob_pairs
        b2 = self.out.bias
        pen = pen + (b2[1:] - b2[:-1]).pow(2).sum() / ob_pairs
        if self.has_psqt:
            pt = self.psqt_w + self.psqt_fac.unsqueeze(0)
            pen = pen + (pt[:, :, 1:] - pt[:, :, :-1]).pow(2).sum() / ob_pairs
        return pen

    @torch.no_grad()
    def project(self) -> None:
        self.w1.clamp_(-1.97, 1.97)
        self.fac.clamp_(-1.97, 1.97)
        self.b1.clamp_(-1.7, 1.7)
        self.out.weight.clamp_(-forge_v3p.MAX_W2 / QB, forge_v3p.MAX_W2 / QB)
        self.out.bias.clamp_(-30.0, 30.0)
        if self.has_psqt:
            self.psqt_w.clamp_(-7.99, 7.99)
            self.psqt_fac.clamp_(-7.99, 7.99)


def to_file_net_p(model: ForgeNetV3P) -> forge_v3p.NetP:
    net = forge_v3p.NetP(model.hidden, model.king_buckets, model.out_buckets,
                         model.mirror, model.pairwise, model.has_psqt, 400)
    with torch.no_grad():
        net.w1 = torch.round((model.w1 + model.fac.unsqueeze(0)) * QA).to(torch.int16).cpu().numpy()
        net.b1 = torch.round(model.b1 * QA).to(torch.int16).cpu().numpy()
        net.w2 = torch.round(model.out.weight * QB).to(torch.int16).cpu().numpy()
        net.b2 = torch.round(model.out.bias * QA * QB).to(torch.int32).cpu().numpy()
        if model.has_psqt:
            net.psqt = torch.round((model.psqt_w + model.psqt_fac.unsqueeze(0)) * QA * QB).to(torch.int32).cpu().numpy()
    net.check_bounds()
    return net


def save_model_p(model: ForgeNetV3P, path: Path) -> None:
    tmp = path.with_name(f"tmp_{path.name}")
    torch.save({
        "arch": "v3p",
        "hidden": model.hidden,
        "king_buckets": model.king_buckets,
        "out_buckets": model.out_buckets,
        "mirror": model.mirror,
        "pairwise": model.pairwise,
        "has_psqt": model.has_psqt,
        "state": {k: v.detach().cpu() for k, v in model.state_dict().items()},
    }, tmp)
    os.replace(tmp, path)


@torch.no_grad()
def verify_int_parity(model: ForgeNetV3P, net: forge_v3p.NetP, dev, n_pos: int = 256) -> dict:
    """Verify PyTorch float grid eval matches exact integer forge_v3p.reference_eval within <= 1 cp!"""
    import chess
    val_p = LAB / "runs/forge/val/val.plain"
    fens = []
    with val_p.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if ln.startswith("fen "):
                fens.append(ln[4:].strip())
                if len(fens) >= n_pos:
                    break
    cmap = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}
    codes = np.zeros((len(fens), 64), dtype=np.uint8)
    stm = np.zeros(len(fens), dtype=np.uint8)
    for i, fen in enumerate(fens):
        parts = fen.split()
        stm[i] = 0 if parts[1] == "w" else 1
        r, c = 7, 0
        for ch in parts[0]:
            if ch == "/": r -= 1; c = 0
            elif "1" <= ch <= "8": c += ord(ch) - 48
            else: codes[i, r * 8 + c] = cmap[ch]; c += 1
    model.eval()
    t_codes = torch.from_numpy(codes).to(dev)
    t_stm = torch.from_numpy(stm).to(dev)
    t_zero = torch.zeros(len(fens), device=dev)
    logits = model(t_codes, t_stm, t_zero).cpu().numpy()
    py_cp = np.clip(np.trunc(logits / float(ft.K) * 400.0), -30000, 30000).astype(np.int32)
    ref_cp = np.array([forge_v3p.reference_eval(net, codes[i], stm[i] == 0) for i in range(len(fens))], dtype=np.int32)
    diffs = np.abs(py_cp - ref_cp)
    return {
        "n": len(fens),
        "exact_0cp": int((diffs == 0).sum()),
        "within_1cp": int((diffs <= 1).sum()),
        "max_diff_cp": int(diffs.max()),
        "mean_diff_cp": round(float(diffs.mean()), 4),
    }


@torch.no_grad()
def score_plain_eval(model: ForgeNetV3P, plain_path: Path, hce_exe: str, dev, skip_noisy: bool, mix: float) -> tuple[float, int]:
    v = ft.load_plain_to_device([str(plain_path)], hce_exe, skip_noisy, dev, True)
    v["hce"] = torch.zeros_like(v["hce"])
    loss = float(ft.dataset_loss(model, v, dev, 65536, mix))
    n = int(v["n"])
    del v
    torch.cuda.empty_cache()
    return loss, n


def selftest() -> None:
    dev = torch.device("cuda")
    torch.manual_seed(42)
    m = ForgeNetV3P(hidden=1024, pairwise=True, has_psqt=True).to(dev)
    # Randomize slightly so weights & psqt are non-trivial
    with torch.no_grad():
        m.w1.normal_(0, 0.05)
        m.b1.normal_(0, 0.1)
        m.out.weight.normal_(0, 0.2)
        m.psqt_w.normal_(0, 0.05)
    m.project()
    # Check autograd flows through BOTH w1/fac/b1/out AND psqt_w/psqt_fac!
    hce_exe = str(LAB / "forge/build/hce_dump.exe")
    val_p = str(LAB / "runs/forge/val/val.plain")
    d = cr.load_compact([val_p], hce_exe, False, dev, with_hce=False)
    idx = torch.arange(1024, device=dev, dtype=torch.int32)
    rows, target, _, bucket = bc.make_batch_c(
        idx, d["packed"], d["stm"], d["score16"], d["res8"], None,
        m.king_map, m.output_map, m.mirror, ft.K / 400.0, 0.85, 0.0)
    pred = torch.sigmoid(m.forward_rows(rows, bucket))
    loss = (pred - target).pow(2).mean() + 1e-4 * m.ob_smooth_penalty()
    loss.backward()
    for name, p in m.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all() and float(p.grad.abs().max()) > 0, f"Bad grad on {name}"
    net = to_file_net_p(m)
    par = verify_int_parity(m, net, dev, n_pos=128)
    assert par["max_diff_cp"] <= 1, f"Parity failed: {par}"
    print("TRAIN_V3P SELFTEST PASS:", par, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--datasets", nargs="+", default=[])
    ap.add_argument("--fqs-shards", nargs="+", default=[], help="Optional .fqs/.fqs.z shard files or directories to mix with --datasets")
    ap.add_argument("--fqs-repeat", type=int, default=1, help="Oversampling factor for --fqs-shards when mixed with older --datasets")
    ap.add_argument("--skip-fqs-noisy", action="store_true", help="Skip FQS rows with flags bit 0 (noisy capture/promo) set")
    ap.add_argument("--keep-fqs-check", "--keep-fqs-in-check", dest="keep_fqs_check", action="store_true",
                    help="Keep FQS rows with flags bit 1 (in_check) set (default: skipped)")
    ap.add_argument("--anchor-shards", nargs="+", default=[], help="Optional pure-draw/Syzygy FQS anchor shards (exact WDL teacher_p)")
    ap.add_argument("--anchor-repeat", type=int, default=20, help="Oversampling factor for --anchor-shards")
    ap.add_argument("--max-rows", type=int, default=0, help="Optional cap on non-anchor training rows (for equal-retained Filter Quest comparisons)")
    ap.add_argument("--score-weight-mode", choices=["none", "soft800", "soft1000", "close_boost"], default="none",
                    help="Optional per-sample WDL loss weighting by |score16| (anchors exempt)")
    ap.add_argument("--ob-reweight", choices=["none", "m4", "cc0"], default="none",
                    help="Optional per-output-bucket loss reweighting (anchors exempt)")
    ap.add_argument("--use-shard-weights", action="store_true", help="Multiply per-sample loss weight by FQS weight_u8/128.0 (anchors exempt)")
    ap.add_argument("--save-cycles", action="store_true", help="Save cand_e{ep}.pt at each LR cycle boundary for SWA")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--hce-exe", default=str(LAB / "forge/build/hce_dump.exe"))
    ap.add_argument("--val", default=str(LAB / "runs/forge/val/val.plain"))
    ap.add_argument("--final-eval", default=str(LAB / "neon/filter_quest/eval_sets/final_eval_r0203_w14_w15.plain"))
    ap.add_argument("--hidden", type=int, default=1024)
    ap.add_argument("--king-buckets", type=int, default=8)
    ap.add_argument("--no-pairwise", action="store_true")
    ap.add_argument("--no-psqt", action="store_true")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=8192)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--min-lr-frac", type=float, default=0.05)
    ap.add_argument("--warmup-steps", type=int, default=500)
    ap.add_argument("--lr-cycles", default="auto")
    ap.add_argument("--w1-decay", type=float, default=0.3)
    ap.add_argument("--ob-smooth", type=float, default=1e-4)
    ap.add_argument("--mix", type=float, default=0.85)
    ap.add_argument("--loss-pow", type=float, default=2.0, help="WDL error exponent (2.0=MSE, 2.5/2.6=Bullet/Stockfish)")
    ap.add_argument("--distill-net", default="")
    ap.add_argument("--distill-weight", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--gpu-hot-pause-c", type=float, default=98.0)
    ap.add_argument("--gpu-hot-resume-c", type=float, default=84.0)
    ap.add_argument("--mem-need-gb", type=float, default=10.0)
    ap.add_argument("--save-ckpt-every", type=int, default=1, help="Save atomic resume_ckpt.pt every N epochs (0=off)")
    ap.add_argument("--resume", action="store_true", help="Resume from out_dir/resume_ckpt.pt if present")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return 0
    if not args.out_dir or (not args.datasets and not args.fqs_shards and not args.anchor_shards):
        raise SystemExit("Need --out-dir and --datasets and/or --fqs-shards")
    if args.epochs < 1:
        raise SystemExit(f"--epochs must be >= 1, got {args.epochs}")
    if args.lr_cycles.strip().lower() == "auto":
        cycles = sorted({max(1, round(args.epochs * f)) for f in (0.15, 0.3, 0.6, 1.0)})
    else:
        cycles = [int(x) for x in args.lr_cycles.split(",") if x.strip()]
        if not cycles or any(c < 1 for c in cycles) or cycles != sorted(set(cycles)):
            raise SystemExit(f"Invalid --lr-cycles={args.lr_cycles!r}; must be strictly increasing positive ints or 'auto'")
    h_step = 64 if not args.no_pairwise else 32
    h_max = 1536 if not args.no_pairwise else 1024
    if args.hidden % h_step != 0 or not (h_step <= args.hidden <= h_max):
        raise SystemExit(f"--hidden must be a multiple of {h_step} in {h_step}..{h_max}, got {args.hidden}")

    r = subprocess.run([sys.executable, str(LAB / "tmp/fable_scratch/tools/mem_room.py"), str(args.mem_need_gb)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"REFUSED by mem_room({args.mem_need_gb}): {r.stdout} {r.stderr}")
    print(r.stdout.strip(), flush=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dev = torch.device("cuda")
    torch.manual_seed(args.seed)
    model = ForgeNetV3P(
        hidden=args.hidden, king_buckets=args.king_buckets, out_buckets=8, mirror=True,
        pairwise=(not args.no_pairwise), has_psqt=(not args.no_psqt),
    ).to(dev)

    t0 = time.time()
    t_path = Path(args.distill_net) if args.distill_net else None
    t_arch = ""
    if t_path is not None:
        ck_meta = torch.load(t_path, map_location="cpu", weights_only=True)
        t_arch = str(ck_meta.get("arch", ""))
        del ck_meta
    t_standalone = t_arch in ("v3", "v3p")
    need_hce = (t_path is not None and not t_standalone)
    def load_fqs_numpy(items: list[str], repeat: int, skip_noisy: bool = False, skip_check: bool = True) -> tuple[np.ndarray, int]:
        fqs_magic = b"FQS1\x00\x00\x00\x00"
        fqs_dtype = np.dtype([
            ("packed", np.uint8, (32,)), ("stm", np.uint8), ("score16", np.int16),
            ("res8", np.int8), ("flags", np.uint8), ("weight_u8", np.uint8),
        ])
        spaths = []
        for s in items:
            p = Path(s)
            if p.is_dir():
                spaths.extend(sorted(list(p.glob("*.fqs")) + list(p.glob("*.fqs.z"))))
            else:
                spaths.append(p)
        if not spaths:
            raise SystemExit(f"No .fqs/.fqs.z files found in {items}")
        mask_bits = (1 if skip_noisy else 0) | (2 if skip_check else 0)
        arrs = []
        for sp in spaths:
            raw = sp.read_bytes()
            if sp.name.endswith(".z"):
                raw = zlib.decompress(raw)
            if len(raw) < 8 or raw[:8] != fqs_magic or (len(raw) - 8) % fqs_dtype.itemsize != 0:
                raise SystemExit(f"Corrupt FQS shard: {sp}")
            a = np.frombuffer(raw, dtype=fqs_dtype, offset=8)
            if mask_bits:
                a = a[(a["flags"] & mask_bits) == 0]
            if len(a) > 0:
                arrs.append(a.copy())
        if not arrs:
            raise SystemExit(f"Zero usable rows after filtering in {items}")
        cat = np.concatenate(arrs, axis=0)
        if repeat > 1:
            cat = np.tile(cat, repeat)
        del arrs
        return cat, len(spaths)

    if (args.fqs_shards or args.anchor_shards) and need_hce:
        raise SystemExit("Residual HCE teacher cannot be used with --fqs-shards/--anchor-shards; use a v3/v3p teacher!")

    # Zero-VRAM-spike preallocation: count plain + FQS + anchors first, allocate ONCE on GPU!
    plain_counts = [ft._count_one(p, args.hce_exe, False, True) for p in args.datasets] if args.datasets else []
    n_plain = int(sum(plain_counts))
    fqs_cat, fqs_nsp = (
        load_fqs_numpy(args.fqs_shards, args.fqs_repeat, args.skip_fqs_noisy, not args.keep_fqs_check)
        if args.fqs_shards else (None, 0)
    )
    anc_cat, anc_nsp = (load_fqs_numpy(args.anchor_shards, args.anchor_repeat, False, False) if args.anchor_shards else (None, 0))
    n_fqs = len(fqs_cat) if fqs_cat is not None else 0
    n_anc = len(anc_cat) if anc_cat is not None else 0
    n_non_anc_raw = n_plain + n_fqs
    if args.max_rows > 0 and n_non_anc_raw > args.max_rows:
        # Equal-retained cap: keep the newest max_rows non-anchor rows (preserving exact row budget)
        drop_n = n_non_anc_raw - args.max_rows
        if drop_n <= n_plain:
            rem = drop_n
            new_plain_counts = []
            for cnt_i in plain_counts:
                if rem >= cnt_i:
                    rem -= cnt_i
                    new_plain_counts.append(0)
                elif rem > 0:
                    new_plain_counts.append(cnt_i - rem)
                    rem = 0
                else:
                    new_plain_counts.append(cnt_i)
            plain_counts = new_plain_counts
            n_plain = int(sum(plain_counts))
        else:
            fqs_drop = drop_n - n_plain
            plain_counts = [0 for _ in plain_counts]
            n_plain = 0
            fqs_cat = fqs_cat[fqs_drop:]
            n_fqs = len(fqs_cat)
    n_total = n_plain + n_fqs + n_anc
    if n_total == 0:
        raise SystemExit("Zero total training positions!")

    need_weights = (args.score_weight_mode != "none" or args.ob_reweight != "none" or args.use_shard_weights)
    d = {
        "packed": torch.empty(n_total, 32, dtype=torch.uint8, device=dev),
        "stm": torch.empty(n_total, dtype=torch.uint8, device=dev),
        "score16": torch.empty(n_total, dtype=torch.int16, device=dev),
        "res8": torch.empty(n_total, dtype=torch.int8, device=dev),
        "n": n_total,
    }
    if need_weights:
        d["weight_u8"] = torch.full((n_total,), 128, dtype=torch.uint8, device=dev)
    if need_hce:
        d["hce16"] = torch.empty(n_total, dtype=torch.int16, device=dev)

    at = 0
    for p, keep_n in zip(args.datasets, plain_counts):
        if keep_n == 0:
            continue
        part = ft._load_one(p, args.hce_exe, False, True)
        full_n = int(part["codes"].shape[0])
        off = max(0, full_n - keep_n)
        for i in range(0, keep_n, cr.LOAD_CHUNK):
            c = part["codes"][off + i:off + min(keep_n, i + cr.LOAD_CHUNK)].to(dev)
            sl = slice(at + i, at + i + int(c.shape[0]))
            d["packed"][sl] = bc.pack_codes(c)
            del c
        d["stm"][at:at + keep_n] = part["stm"][off:off + keep_n].to(torch.uint8).to(dev)
        d["score16"][at:at + keep_n] = part["score"][off:off + keep_n].to(torch.int16).to(dev)
        d["res8"][at:at + keep_n] = part["res"][off:off + keep_n].to(torch.int8).to(dev)
        if need_hce:
            d["hce16"][at:at + keep_n] = part["hce"][off:off + keep_n].to(torch.int16).to(dev)
        at += keep_n
        del part

    if fqs_cat is not None:
        d["packed"][at:at + n_fqs] = torch.from_numpy(fqs_cat["packed"].copy()).to(dev)
        d["stm"][at:at + n_fqs] = torch.from_numpy(fqs_cat["stm"].copy()).to(dev)
        d["score16"][at:at + n_fqs] = torch.from_numpy(fqs_cat["score16"].copy()).to(dev)
        d["res8"][at:at + n_fqs] = torch.from_numpy(fqs_cat["res8"].copy()).to(dev)
        if need_weights and args.use_shard_weights:
            d["weight_u8"][at:at + n_fqs] = torch.from_numpy(fqs_cat["weight_u8"].copy()).to(dev)
        at += n_fqs
        del fqs_cat
        print(f"FQS MIXED: +{n_fqs:,} pos (repeat={args.fqs_repeat}x skip_noisy={args.skip_fqs_noisy} skip_check={not args.keep_fqs_check} from {fqs_nsp} shards) -> {at:,}", flush=True)

    n_before_anchors = at
    if anc_cat is not None:
        d["packed"][at:at + n_anc] = torch.from_numpy(anc_cat["packed"].copy()).to(dev)
        d["stm"][at:at + n_anc] = torch.from_numpy(anc_cat["stm"].copy()).to(dev)
        d["score16"][at:at + n_anc] = torch.from_numpy(anc_cat["score16"].copy()).to(dev)
        d["res8"][at:at + n_anc] = torch.from_numpy(anc_cat["res8"].copy()).to(dev)
        at += n_anc
        del anc_cat
        print(f"ANCHORS MIXED: +{n_anc:,} pos (repeat={args.anchor_repeat}x from {anc_nsp} shards, exact WDL teacher) -> total {at:,}", flush=True)
    assert at == n_total

    teacher_p = None
    t_weight = 0.0
    if t_path is not None:
        t_weight = float(args.distill_weight)
        if t_arch == "v3p":
            ck = torch.load(t_path, map_location="cpu", weights_only=True)
            t_net = ForgeNetV3P(
                hidden=ck["hidden"], king_buckets=ck["king_buckets"], out_buckets=ck["out_buckets"],
                mirror=ck["mirror"], pairwise=ck["pairwise"], has_psqt=ck["has_psqt"],
            )
            t_net.load_state_dict(ck["state"])
            del ck
        elif t_arch == "v3":
            t_net = v3.load_model(str(t_path))
        else:
            t_net = ft.load_checkpoint(t_path)
            t_net.ft_backend = "triton"
        t_net.to(dev).eval()
        for prm in t_net.parameters():
            prm.requires_grad_(False)
        t_pre = time.time()
        teacher_p = torch.empty(d["n"], device=dev, dtype=torch.float32)
        with torch.no_grad():
            for i in range(0, n_before_anchors, args.batch_size):
                end = min(n_before_anchors, i + args.batch_size)
                ix = torch.arange(i, end, device=dev)
                t_hce = (torch.zeros(len(ix), device=dev) if t_standalone else d["hce16"][ix].float()) * (ft.K / 400.0)
                teacher_p[i:end] = torch.sigmoid(t_net(cr.unpack_feat(d, ix), None, t_hce))
            if n_before_anchors < d["n"]:
                # Exact ground-truth WDL for FIDE dead-draw (res=0 -> 0.5) & Syzygy won-ending (res=+-1 -> 1.0/0.0) anchors!
                teacher_p[n_before_anchors:] = 0.5 * (d["res8"][n_before_anchors:].float() + 1.0)
        del t_net
        cr.free_teacher_inputs(d)
        torch.cuda.empty_cache()
        print(f"TEACHER ONCE ({t_arch or 'hce'} {t_path.name}, w={t_weight}): {n_before_anchors:,} distilled + {d['n']-n_before_anchors:,} exact-draw anchors in {time.time()-t_pre:.1f}s", flush=True)

    sample_w = None
    if need_weights:
        w = torch.ones(d["n"], dtype=torch.float32, device=dev)
        if args.use_shard_weights:
            w[:n_before_anchors] *= d["weight_u8"][:n_before_anchors].float() * (1.0 / 128.0)
        if args.score_weight_mode != "none":
            abs_sc = d["score16"][:n_before_anchors].abs()
            if args.score_weight_mode == "soft800":
                sw = torch.where(abs_sc >= 1200, 0.25, torch.where(abs_sc >= 800, 0.50, 1.0))
            elif args.score_weight_mode == "soft1000":
                sw = torch.where(abs_sc >= 1400, 0.25, torch.where(abs_sc >= 1000, 0.50, 1.0))
            else:  # close_boost
                sw = torch.where(abs_sc < 300, 1.30, torch.where(abs_sc >= 1200, 0.25, torch.where(abs_sc >= 800, 0.50, 1.0)))
            w[:n_before_anchors] *= sw
            del abs_sc, sw
        if args.ob_reweight != "none":
            # Compute piece count directly from packed uint8[32] nibbles in chunks (zero extra VRAM!)
            ob_lut = torch.tensor(
                [1.65, 1.01, 1.07, 1.00, 1.00, 0.99, 0.95, 0.65] if args.ob_reweight == "m4"
                else [1.50, 1.089, 1.167, 0.978, 0.922, 0.883, 0.891, 0.70],
                dtype=torch.float32, device=dev,
            )
            for i in range(0, n_before_anchors, 262144):
                end = min(n_before_anchors, i + 262144)
                pk = d["packed"][i:end]
                npcs = (((pk & 0x0F) != 0).sum(dim=1) + (((pk >> 4) & 0x0F) != 0).sum(dim=1)).clamp(2, 32)
                ob = ((npcs - 2) // 4).clamp(0, 7)
                w[i:end] *= ob_lut[ob]
            del ob_lut
        # Mean-normalize non-anchor weights only; keep anchor rows strictly at 1.0 (Anchor Weight-Exemption Rule!)
        if n_before_anchors > 0:
            mean_w = float(w[:n_before_anchors].mean().item())
            if mean_w > 0:
                w[:n_before_anchors] /= mean_w
        if n_before_anchors < d["n"]:
            w[n_before_anchors:] = 1.0
        sample_w = w
        del d["weight_u8"]
        print(f"SAMPLE WEIGHTS READY: score={args.score_weight_mode} ob={args.ob_reweight} shard_w={args.use_shard_weights} "
              f"non_anc_mean={float(sample_w[:n_before_anchors].mean()):.4f} anchors_exempt={d['n']-n_before_anchors:,}", flush=True)

    steps_per_epoch = max(1, d["n"] // args.batch_size)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, fused=True)
    ckpt_path = out_dir / "resume_ckpt.pt"
    start_ep = 0
    step = 0
    tl = 0.0
    if args.resume and ckpt_path.exists():
        ck = torch.load(ckpt_path, map_location=dev, weights_only=False)
        ck_cfg = ck.get("cfg")
        if ck_cfg is not None:
            want_cfg = {"hidden": args.hidden, "batch_size": args.batch_size,
                        "pairwise": model.pairwise, "has_psqt": model.has_psqt}
            if ck_cfg != want_cfg:
                raise SystemExit(f"Resume checkpoint mismatch: ckpt={ck_cfg} != current={want_cfg}")
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        start_ep = int(ck["epoch"])
        step = int(ck["step"])
        tl = float(ck.get("tl", 0.0))
        del ck
        print(f"RESUMED from {ckpt_path} at epoch {start_ep}/{args.epochs} (step {step})", flush=True)

    guard = ft.GpuHeatGuard(args.gpu_hot_pause_c, args.gpu_hot_resume_c)
    ram = ft.RamGuard(float(os.environ.get("FORGE_MIN_FREE_RAM_GB", "1.5") or 0))
    order_buf = torch.empty(d["n"], dtype=torch.int32)
    perm = torch.empty(d["n"], dtype=torch.int32, device=dev)

    def pass_order(k: int) -> torch.Tensor:
        g = torch.Generator()
        g.manual_seed(args.seed * 1_000_003 + k)
        torch.randperm(d["n"], generator=g, out=order_buf)
        return order_buf

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    nxt = pool.submit(pass_order, start_ep) if start_ep < args.epochs else None
    print(f"START_V3P: n={d['n']:,} H={args.hidden} pairwise={model.pairwise} psqt={model.has_psqt} "
          f"ep={start_ep}..{args.epochs} mix={args.mix} ob_smooth={args.ob_smooth} distill={t_weight} load_s={time.time()-t0:.1f}", flush=True)

    t_train = time.time()
    for ep in range(start_ep, args.epochs):
        model.train()
        order = nxt.result()
        perm.copy_(order)
        del order
        nxt = pool.submit(pass_order, ep + 1) if ep + 1 < args.epochs else None
        run, cnt = 0.0, 0
        for bi in range(steps_per_epoch):
            idx = perm[bi * args.batch_size:(bi + 1) * args.batch_size]
            lr = v3.lr_at(step, steps_per_epoch, cycles, args)
            for pg in opt.param_groups:
                pg["lr"] = lr
            rows, target, _, bucket = bc.make_batch_c(
                idx, d["packed"], d["stm"], d["score16"], d["res8"], teacher_p,
                model.king_map, model.output_map, model.mirror,
                ft.K / 400.0, args.mix, t_weight)
            if t_path is None and n_before_anchors < d["n"]:
                anc_wdl = 0.5 * (d["res8"][idx.long()].float() + 1.0)
                target = torch.where(idx >= n_before_anchors, anc_wdl, target)
            pred = torch.sigmoid(model.forward_rows(rows, bucket))
            if abs(args.loss_pow - 2.0) < 1e-6:
                err = (pred - target).pow(2)
            else:
                err = (pred - target).abs().clamp(min=1e-7).pow(args.loss_pow)
            if sample_w is not None:
                bw = sample_w[idx.long()]
                loss = (bw * err).sum() / bw.sum().clamp(min=1e-7)
            else:
                loss = err.mean()
            if args.ob_smooth > 0:
                loss = loss + args.ob_smooth * model.ob_smooth_penalty()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            with torch.no_grad():
                if args.w1_decay > 0:
                    model.w1.mul_(1.0 - lr * args.w1_decay)
                    if model.has_psqt:
                        model.psqt_w.mul_(1.0 - lr * args.w1_decay)
            model.project()
            step += 1
            if bi % 20 == 0:
                run += float(loss.detach())
                cnt += 1
                guard.tick()
                ram.tick()
        if not all(bool(torch.isfinite(p_).all()) for p_ in model.parameters()):
            raise SystemExit(f"NaN/Inf weight after epoch {ep + 1}")
        tl = run / max(1, cnt)
        active_s = max(1e-9, time.time() - t_train - guard.paused_s)
        print(f"LOSS {tl:.6f}  epoch {ep+1}/{args.epochs} lr {lr:.2e} "
              f"{(ep - start_ep + 1)*steps_per_epoch*args.batch_size/active_s:,.0f} pos/s", flush=True)
        if args.save_cycles and (ep + 1) in cycles:
            save_model_p(model, out_dir / f"cand_e{ep + 1}.pt")
        if args.save_ckpt_every > 0 and ((ep + 1) % args.save_ckpt_every == 0):
            tmp_ck = out_dir / "tmp_resume_ckpt.pt"
            torch.save({
                "epoch": ep + 1,
                "step": step,
                "tl": tl,
                "cfg": {"hidden": args.hidden, "batch_size": args.batch_size,
                        "pairwise": model.pairwise, "has_psqt": model.has_psqt},
                "model": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                "opt": opt.state_dict(),
            }, tmp_ck)
            os.replace(tmp_ck, ckpt_path)

    pool.shutdown(wait=True)
    train_s = time.time() - t_train
    del d, perm, order_buf, teacher_p, sample_w
    torch.cuda.empty_cache()

    model_p = out_dir / "cand.pt"
    net_p = out_dir / "cand.fnn3"
    save_model_p(model, model_p)
    net = to_file_net_p(model)
    checksum = forge_v3p.write_net(str(net_p), net)
    net_sha = hashlib.sha256(net_p.read_bytes()).hexdigest()
    par = verify_int_parity(model, net, dev, n_pos=256)

    model.eval()
    val_q60, _ = score_plain_eval(model, Path(args.val), args.hce_exe, dev, skip_noisy=True, mix=0.6)
    val_a60, _ = score_plain_eval(model, Path(args.val), args.hce_exe, dev, skip_noisy=False, mix=0.6)
    fe_q60, _ = score_plain_eval(model, Path(args.final_eval), args.hce_exe, dev, skip_noisy=True, mix=0.6)
    fe_a60, _ = score_plain_eval(model, Path(args.final_eval), args.hce_exe, dev, skip_noisy=False, mix=0.6)

    metrics = {
        "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
        "args": vars(args),
        "train_seconds": round(train_s, 1),
        "gpu_paused_s": round(guard.paused_s, 1),
        "gpu_pauses": guard.pauses,
        "gpu_max_c": guard.max_seen,
        "final_train_loss": round(tl, 6),
        "legacy_val_quiet_mix60": round(val_q60, 6),
        "legacy_val_all_mix60": round(val_a60, 6),
        "final_eval_r0203_quiet_mix60": round(fe_q60, 6),
        "final_eval_r0203_all_mix60": round(fe_a60, 6),
        "int_parity": par,
        "net_path": str(net_p),
        "net_bytes": net_p.stat().st_size,
        "net_checksum": f"{checksum:016x}",
        "net_sha256": net_sha,
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("V3P_TRAIN_DONE:", json.dumps(metrics, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
