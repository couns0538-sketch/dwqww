#!/usr/bin/env python3
"""NNUE v3 trainer / exporter / parity / scorer (job FB1 M3, extended by FB2-J1). CPU torch, small RAM.

Architecture (matches include/forge/nnue_v3.hpp):
  per perspective: king-bucketed HalfKA features -> hidden (H) accumulator, SCReLU; output bucket by piece count.
  A factoriser block (768 x H) shared by every king bucket is added to each bucket's weights during training and
  merged into the exported per-bucket weights.
Quantisation-aware training: every forward uses the engine's integer grid (straight-through rounding of the
merged first-layer weights to 1/QA, b1 to 1/QA, w2 to 1/QB clipped to +-127/QB, b2 to 1/(QA*QB)), and after every
step the parameters are clipped to the exportable ranges, so the exported int16/int32 file evaluates (up to the
engine's truncating divisions) exactly like the training forward.

Data: FPOS v1 (.pos: 16-byte header, rows x 32 bytes of 4-bit piece codes a1..h8, rows x int16 score, rows x u8
meta with bit0 = side to move (1 = black), bits1-2 = white result * 2) and FHCE v1 (.hce: header + rows x int16
hand-crafted eval); the formats of the Forge self-play shards.

Commands:
  train   --pos-glob G --hce-dir D --out DIR [--hidden 512 --king-buckets 8 --output-buckets 8 --mirror --residual
          --no-factorizer --steps N --batch 8192 --lr 1e-3 --lr-schedule cosine --warmup-steps 500
          --blend-schedule linear --blend-start 0.9 --blend-end 0.6 --seed 1 --eval-scale 400]
          FB2-J1 additions: --resume DIR/ckpt.pt (exact model / optimiser / schedule / RNG state), --ckpt-every-minutes M
          (checkpoint = ckpt.pt + exported ckNN_stepS.fnn3 + exact holdout score per phase (--exact-pos/--exact-hce)
          + engine parity (--parity-tool/--parity-fens) + status.json), --target-loss X and --plateau N (stop rules),
          --max-minutes M (chunk length; the run continues with --resume).
  export  --model DIR/model.pt --net OUT.fnn3
  parity  --model DIR/model.pt --net NET.fnn3 --fens F --engine-out E   (engine int == trainer int, float within 2 cp)
  score   --net NET.fnn3 --pos P --hce H [--max-rows N] [--phases]        (holdout MSE at blends 1.0/0.6/0.8)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fable_nnue_v3 as v3  # noqa: E402

K = 2.25
QA = v3.QA
QB = v3.QB
PHASES = 8


# ---------------- data ----------------

def read_fpos(pos_path, hce_path=None, max_rows=None):
    data = np.memmap(pos_path, np.uint8, "r")
    if bytes(data[:4]) != b"FPOS":
        raise SystemExit(f"{pos_path}: not an FPOS file")
    total = int(np.frombuffer(bytes(data[8:16]), "<u8")[0])
    n = total if max_rows is None else min(total, max_rows)
    boards = np.asarray(np.memmap(pos_path, np.uint8, "r", 16, (n, 32)))
    score = np.asarray(np.memmap(pos_path, "<i2", "r", 16 + 32 * total, (n,))).astype(np.int64)
    meta = np.asarray(np.memmap(pos_path, np.uint8, "r", 16 + 34 * total, (n,))).astype(np.int64)
    hce = None
    if hce_path is not None:
        hdata = np.memmap(hce_path, np.uint8, "r")
        if bytes(hdata[:4]) != b"FHCE":
            raise SystemExit(f"{hce_path}: not an FHCE file")
        hce = np.asarray(np.memmap(hce_path, "<i2", "r", 16, (n,))).astype(np.int64)
    codes = np.empty((n, 64), np.uint8)
    codes[:, 0::2] = boards & 15
    codes[:, 1::2] = boards >> 4
    return {"codes": codes, "score": score, "meta": meta, "hce": hce, "n": n}


class ShardStream:
    """Cross-shard sampling with a bounded buffer: K chunks of `chunk_rows` consecutive rows, each from a random
    shard at a random offset; every `refresh_every` batches the oldest chunk is replaced. Batches draw rows
    uniformly from the whole buffer, so each batch mixes K shards / game regions. Memory: about 90 bytes per
    buffered row (2M rows = 180 MB)."""

    def __init__(self, pos_files, hce_files, chunk_rows, chunks, refresh_every, rng, need_hce, shard_weighting="rows"):
        self.pos_files = pos_files
        self.hce_files = hce_files
        self.chunk_rows = chunk_rows
        self.refresh_every = refresh_every
        self.rng = rng
        self.need_hce = need_hce
        self.rows_of = []
        for f in pos_files:
            data = np.memmap(f, np.uint8, "r")
            if bytes(data[:4]) != b"FPOS":
                raise SystemExit(f"{f}: not an FPOS file")
            self.rows_of.append(int(np.frombuffer(bytes(data[8:16]), "<u8")[0]))
        # "rows": a shard is chosen with probability proportional to its row count (every row equally likely
        # over the run, like the production trainer); "uniform": every shard equally likely (the first-net and
        # standalone runs of 2026-10-28 used this, which over-represents the small early shards).
        rows = np.asarray(self.rows_of, np.float64)
        self.shard_p = rows / rows.sum() if shard_weighting == "rows" else np.full(len(rows), 1.0 / len(rows))
        self.buffers = [self._load_chunk() for _ in range(chunks)]
        self.next_replace = 0
        self.batches = 0
        self.chunks_loaded = chunks

    def _load_chunk(self):
        k = int(self.rng.choice(len(self.pos_files), p=self.shard_p))
        total = self.rows_of[k]
        n = min(self.chunk_rows, total)
        start = int(self.rng.integers(0, total - n + 1))
        pos = self.pos_files[k]
        boards = np.asarray(np.memmap(pos, np.uint8, "r", 16 + 32 * start, (n, 32)))
        score = np.asarray(np.memmap(pos, "<i2", "r", 16 + 32 * total + 2 * start, (n,))).astype(np.int16)
        meta = np.asarray(np.memmap(pos, np.uint8, "r", 16 + 34 * total + start, (n,)))
        hce = None
        if self.need_hce:
            hce = np.asarray(np.memmap(self.hce_files[k], "<i2", "r", 16 + 2 * start, (n,))).astype(np.int16)
        codes = np.empty((n, 64), np.uint8)
        codes[:, 0::2] = boards & 15
        codes[:, 1::2] = boards >> 4
        return {"codes": codes, "score": score, "meta": meta, "hce": hce, "n": n, "shard": k, "start": start}

    def batch(self, size):
        sizes = np.array([b["n"] for b in self.buffers])
        total = int(sizes.sum())
        flat = self.rng.integers(0, total, size=size)
        bounds = np.cumsum(sizes)
        which = np.searchsorted(bounds, flat, side="right")
        local = flat - (bounds - sizes)[which]
        order = np.argsort(which, kind="stable")
        which, local = which[order], local[order]
        codes = np.empty((size, 64), np.uint8)
        score = np.empty(size, np.int64)
        meta = np.empty(size, np.int64)
        hce = np.zeros(size, np.int64)
        for k in np.unique(which):
            sel = which == k
            rows = local[sel]
            b = self.buffers[k]
            codes[sel] = b["codes"][rows]
            score[sel] = b["score"][rows]
            meta[sel] = b["meta"][rows]
            if b["hce"] is not None:
                hce[sel] = b["hce"][rows]
        self.batches += 1
        if self.batches % self.refresh_every == 0:
            self.buffers[self.next_replace] = self._load_chunk()
            self.next_replace = (self.next_replace + 1) % len(self.buffers)
            self.chunks_loaded += 1
        return codes, score, meta, hce


def codes_from_fen(fen):
    import chess
    board = chess.Board(fen)
    codes = np.zeros(64, np.uint8)
    for sq, piece in board.piece_map().items():
        codes[sq] = piece.piece_type + (0 if piece.color else 6)
    return codes, 0 if board.turn else 1


SQ = np.arange(64)


def perspective_indices(codes, white, king_map, mirror, kb, pad):
    """Feature indices [B, 64] (merged table rows, pad for empty squares) of perspective `white` (bool)."""
    occupied = codes != 0
    if white:
        rel = (codes >= 7).astype(np.int64)
        sq = np.broadcast_to(SQ, codes.shape)
        king = np.argmax(codes == 6, axis=1)
        kr = king
    else:
        rel = ((codes >= 1) & (codes <= 6)).astype(np.int64)
        sq = np.broadcast_to(SQ ^ 56, codes.shape)
        king = np.argmax(codes == 12, axis=1)
        kr = king ^ 56
    ptype = (codes.astype(np.int64) - 1) % 6
    bucket = king_map[kr]
    flip = np.where(mirror & ((kr & 7) >= 4), 7, 0)
    feat = (rel * 6 + ptype) * 64 + (sq ^ flip[:, None])
    idx = bucket[:, None] * 768 + feat
    return np.where(occupied, idx, pad)


def batch_features(codes, meta, cfg):
    kb = cfg["king_buckets"]
    pad = kb * 768
    king_map = np.asarray(cfg["king_map"], np.int64)
    output_map = np.asarray(cfg["output_map"], np.int64)
    w = perspective_indices(codes, True, king_map, cfg["mirror"], kb, pad)
    b = perspective_indices(codes, False, king_map, cfg["mirror"], kb, pad)
    stm = (meta & 1).astype(bool)
    us = np.where(stm[:, None], b, w)
    them = np.where(stm[:, None], w, b)
    pieces = np.minimum((codes != 0).sum(axis=1), 32)
    ob = output_map[pieces]
    return us, them, ob


def phase_of_codes(codes):
    """Phase bin 0..7 by piece count (the 8-bucket output map), for per-phase holdout reporting."""
    pieces = np.minimum((codes != 0).sum(axis=1), 32)
    return np.asarray(v3.output_layout(PHASES), np.int64)[pieces]


# ---------------- model ----------------

def build_model(cfg, torch):
    import torch.nn as nn

    class Model(nn.Module):
        def __init__(self):
            super().__init__()
            H, kb, ob = cfg["hidden"], cfg["king_buckets"], cfg["output_buckets"]
            g = torch.Generator().manual_seed(cfg["seed"])
            self.w1 = nn.Parameter(torch.randn(kb * 768, H, generator=g) * cfg["init_scale"])
            self.wf = nn.Parameter(torch.zeros(768, H)) if cfg["factorizer"] else None
            self.b1 = nn.Parameter(torch.zeros(H))
            self.w2 = nn.Parameter(torch.randn(ob, 2 * H, generator=g) * (0.5 / np.sqrt(H)))
            self.b2 = nn.Parameter(torch.zeros(ob))
            # FB2-J7 v4 prototypes (trainer only, no v3 file): pairwise us*them output term and a second layer
            self.w3 = nn.Parameter(torch.zeros(ob, H)) if cfg.get("pairwise") else None
            L2 = int(cfg.get("l2", 0) or 0)
            self.l2w = nn.Parameter(torch.randn(L2, 2 * H, generator=g) * (1.0 / np.sqrt(2 * H))) if L2 else None
            self.l2b = nn.Parameter(torch.zeros(L2)) if L2 else None
            self.l2o = nn.Parameter(torch.randn(ob, L2, generator=g) * (0.5 / np.sqrt(L2))) if L2 else None

        def merged_w1(self):
            if self.wf is None:
                return self.w1
            kb, H = cfg["king_buckets"], cfg["hidden"]
            return (self.w1.view(kb, 768, H) + self.wf.view(1, 768, H)).view(kb * 768, H)

        @staticmethod
        def fq(x, q):
            return x + (torch.round(x * q) / q - x).detach()

        def quantised(self):
            """Fake-quantised parameters on the engine grid (float tensors)."""
            w1 = self.fq(self.merged_w1(), QA)
            b1 = self.fq(self.b1, QA)
            w2 = torch.clamp(self.fq(self.w2, QB), -127.0 / QB, 127.0 / QB)
            b2 = self.fq(self.b2, QA * QB)
            return w1, b1, w2, b2

        def forward(self, us, them, ob):
            import torch.nn.functional as F
            w1, b1, w2, b2 = self.quantised()
            table = torch.cat([w1, torch.zeros(1, w1.shape[1], dtype=w1.dtype)], dim=0)
            pad = w1.shape[0]
            acc_us = F.embedding_bag(us, table, mode="sum", padding_idx=pad) + b1
            acc_them = F.embedding_bag(them, table, mode="sum", padding_idx=pad) + b1
            s_us = torch.clamp(acc_us, 0.0, 1.0) ** 2
            s_them = torch.clamp(acc_them, 0.0, 1.0) ** 2
            w2_sel = w2[ob]
            both = torch.cat([s_us, s_them], dim=1)
            if self.l2w is not None:
                hidden = torch.clamp(both @ self.l2w.t() + self.l2b, 0.0, 1.0)
                out = (hidden * self.l2o[ob]).sum(dim=1) + b2[ob]
            else:
                out = (both * w2_sel).sum(dim=1) + b2[ob]
            if self.w3 is not None:
                out = out + (s_us * s_them * self.w3[ob]).sum(dim=1)
            return out * cfg["eval_scale"]   # centipawns (float)

        def clip(self):
            with torch.no_grad():
                lim = 1.98 if self.wf is None else 0.99
                self.w1.clamp_(-lim, lim)
                if self.wf is not None:
                    self.wf.clamp_(-0.99, 0.99)
                self.b1.clamp_(-1.98, 1.98)
                self.w2.clamp_(-127.0 / QB, 127.0 / QB)

    return Model()


def export_net(model, cfg, path, torch):
    with torch.no_grad():
        w1 = torch.round(model.merged_w1() * QA).clamp(-32767, 32767).to(torch.int16).numpy()
        b1 = torch.round(model.b1 * QA).clamp(-32767, 32767).to(torch.int16).numpy()
        w2 = torch.round(model.w2 * QB).clamp(-127, 127).to(torch.int16).numpy()
        b2 = torch.round(model.b2 * QA * QB).to(torch.int32).numpy()
    net = v3.Net()
    net.hidden = cfg["hidden"]
    net.king_buckets = cfg["king_buckets"]
    net.output_buckets = cfg["output_buckets"]
    net.eval_scale = cfg["eval_scale"]
    net.flags = (v3.FLAG_MIRROR if cfg["mirror"] else 0) | (v3.FLAG_RESIDUAL if cfg["residual"] else 0)
    net.king_map = list(cfg["king_map"])
    net.output_map = list(cfg["output_map"])
    net.w1 = w1.reshape(cfg["king_buckets"], 768, cfg["hidden"])
    net.b1 = b1
    net.w2 = w2
    net.b2 = b2
    max_w1 = int(np.abs(w1).max())
    max_b1 = int(np.abs(b1).max())
    if max_b1 + 32 * max_w1 > 32767:
        raise SystemExit(f"export: accumulator bound violated ({max_b1} + 32*{max_w1})")
    checksum = v3.write_net(path, net)
    return checksum, max_w1, max_b1, int(np.abs(w2).max())


def loss_fn(cp, score, meta, hce, cfg, torch, blend=None):
    logit = cp * (K / 400.0)
    if cfg["residual"]:
        logit = logit + hce * (K / 400.0)
    pred = torch.sigmoid(logit)
    teacher = torch.sigmoid(torch.clamp(score * (K / 400.0), -40.0, 40.0))
    stm = (meta & 1).to(torch.float32)
    white = (meta >> 1).to(torch.float32) * 0.5
    stm_res = torch.where(stm == 0, white, 1.0 - white)
    b = cfg["blend"] if blend is None else blend
    target = b * teacher + (1.0 - b) * stm_res
    return torch.mean((pred - target) ** 2)


def make_cfg(args):
    return {
        "hidden": args.hidden, "king_buckets": args.king_buckets, "output_buckets": args.output_buckets,
        "mirror": bool(args.mirror), "residual": bool(args.residual), "factorizer": not args.no_factorizer,
        "eval_scale": args.eval_scale, "blend": args.blend, "seed": args.seed, "init_scale": args.init_scale,
        "king_map": v3.king_layout(args.king_buckets), "output_map": v3.output_layout(args.output_buckets),
        "l2": int(getattr(args, "l2", 0) or 0), "pairwise": bool(getattr(args, "pairwise", False)),
    }


def tensors_from(codes, score, meta, hce, cfg, torch):
    us, them, ob = batch_features(codes, meta, cfg)
    return {
        "us": torch.from_numpy(us), "them": torch.from_numpy(them), "ob": torch.from_numpy(ob),
        "score": torch.from_numpy(np.asarray(score).astype(np.float32)),
        "meta": torch.from_numpy(np.asarray(meta).astype(np.int64)),
        "hce": torch.from_numpy(np.asarray(hce).astype(np.float32)),
    }


# ---------------- schedules ----------------

def lr_at(step, args):
    if args.warmup_steps and step < args.warmup_steps:
        return args.lr * (step + 1) / args.warmup_steps
    if args.lr_schedule == "cosine":
        frac = min(step / max(args.steps, 1), 1.0)
        return args.lr_final + 0.5 * (args.lr - args.lr_final) * (1.0 + np.cos(np.pi * frac))
    if args.lr_schedule == "linear":
        frac = min(step / max(args.steps, 1), 1.0)
        return args.lr + (args.lr_final - args.lr) * frac
    return args.lr


def blend_at(step, args):
    """WDL-lambda schedule: the teacher-score weight moves from --blend-start to --blend-end over --steps
    (idea: nnue-pytorch's start_lambda / end_lambda; the metric blend b0.6 is the end value)."""
    if args.blend_schedule == "constant":
        return args.blend
    b0 = args.blend if args.blend_start is None else args.blend_start
    b1 = args.blend if args.blend_end is None else args.blend_end
    frac = min(step / max(args.steps, 1), 1.0)
    if args.blend_schedule == "linear":
        return b0 + (b1 - b0) * frac
    return b1 + 0.5 * (b0 - b1) * (1.0 + np.cos(np.pi * frac))   # cosine


# ---------------- exact scoring and parity (shared by `score`, `parity` and the checkpoints) ----------------

def score_net_numpy(net, data, cfg_residual, chunk=4096, phases=False):
    """Holdout MSE (blends 1.0 / 0.6 / 0.8) of a v3 file with exact integer emulation vectorised per chunk;
    with phases=True also the b0.6 MSE and row count per phase bin (piece-count buckets)."""
    H = net.hidden
    w1 = np.concatenate([net.w1.reshape(-1, H), np.zeros((1, H), np.int64)], axis=0).astype(np.int16)
    b1 = net.b1.astype(np.int32)
    cfg = {"king_buckets": net.king_buckets, "mirror": net.mirror, "king_map": net.king_map, "output_map": net.output_map}
    sums = {1.0: 0.0, 0.6: 0.0, 0.8: 0.0}
    phase_sum = np.zeros(PHASES)
    phase_n = np.zeros(PHASES, np.int64)
    n = data["n"]
    for start in range(0, n, chunk):
        rows = np.arange(start, min(start + chunk, n))
        codes = data["codes"][rows]
        meta = data["meta"][rows]
        us, them, ob = batch_features(codes, meta, cfg)
        # int32 accumulators, one gather per square (small memory footprint); exact like the engine
        acc_us = np.broadcast_to(b1, (len(rows), H)).astype(np.int32)
        acc_them = acc_us.copy()
        for k in range(64):
            acc_us += w1[us[:, k]]
            acc_them += w1[them[:, k]]
        a = np.clip(acc_us, 0, QA).astype(np.int64)
        b = np.clip(acc_them, 0, QA).astype(np.int64)
        w2 = net.w2[ob]
        total = (a * a * w2[:, :H]).sum(axis=1) + (b * b * w2[:, H:]).sum(axis=1)
        out = np.trunc(total / QA).astype(np.int64) + net.b2[ob]
        cp = np.trunc(out * net.eval_scale / (QA * QB)).astype(np.int64)
        cp = np.clip(cp, -30000, 30000)
        logit = cp * (K / 400.0)
        if cfg_residual:
            logit = logit + data["hce"][rows] * (K / 400.0)
        pred = 1.0 / (1.0 + np.exp(-logit))
        teacher = 1.0 / (1.0 + np.exp(-np.clip(data["score"][rows] * (K / 400.0), -40.0, 40.0)))
        stm = meta & 1
        white = (meta >> 1) * 0.5
        stm_res = np.where(stm == 0, white, 1.0 - white)
        for bl in sums:
            target = bl * teacher + (1.0 - bl) * stm_res
            err = (pred - target) ** 2
            sums[bl] += float(np.sum(err))
            if bl == 0.6 and phases:
                ph = phase_of_codes(codes)
                phase_sum += np.bincount(ph, weights=err, minlength=PHASES)
                phase_n += np.bincount(ph, minlength=PHASES)
    result = {f"mse_b{bl}": sums[bl] / n for bl in sums}
    if phases:
        result["phase_rows"] = phase_n.tolist()
        result["phase_mse_b0.6"] = [float(phase_sum[i] / phase_n[i]) if phase_n[i] else None for i in range(PHASES)]
    return result


def float_score(model, data, cfg, torch, chunk=8192):
    """Holdout MSE (blends 1.0 / 0.6 / 0.8, per-phase b0.6) with the float training forward (FB2-J7 prototypes
    that have no integer file; for v3 nets it differs from the exact score only by the truncating divisions)."""
    sums = {1.0: 0.0, 0.6: 0.0, 0.8: 0.0}
    phase_sum = np.zeros(PHASES)
    phase_n = np.zeros(PHASES, np.int64)
    n = data["n"]
    model.eval()
    with torch.no_grad():
        for start in range(0, n, chunk):
            rows = np.arange(start, min(start + chunk, n))
            codes = data["codes"][rows]
            meta = data["meta"][rows]
            t = tensors_from(codes, data["score"][rows], meta, data["hce"][rows] if data["hce"] is not None else np.zeros(len(rows), np.int64), cfg, torch)
            cp = model(t["us"], t["them"], t["ob"]).numpy().astype(np.float64)
            logit = cp * (K / 400.0)
            if cfg["residual"]:
                logit = logit + data["hce"][rows] * (K / 400.0)
            pred = 1.0 / (1.0 + np.exp(-logit))
            teacher = 1.0 / (1.0 + np.exp(-np.clip(data["score"][rows] * (K / 400.0), -40.0, 40.0)))
            stm = meta & 1
            white = (meta >> 1) * 0.5
            stm_res = np.where(stm == 0, white, 1.0 - white)
            for bl in sums:
                target = bl * teacher + (1.0 - bl) * stm_res
                err = (pred - target) ** 2
                sums[bl] += float(np.sum(err))
                if bl == 0.6:
                    ph = phase_of_codes(codes)
                    phase_sum += np.bincount(ph, weights=err, minlength=PHASES)
                    phase_n += np.bincount(ph, minlength=PHASES)
    model.train()
    result = {f"mse_b{bl}": sums[bl] / n for bl in sums}
    result["phase_rows"] = phase_n.tolist()
    result["phase_mse_b0.6"] = [float(phase_sum[i] / phase_n[i]) if phase_n[i] else None for i in range(PHASES)]
    return result


def parity_check(model, cfg, net_path, fens_path, engine_lines, torch):
    """engine int (forge_nnue_v3_tool eval output lines) == trainer int (integer emulation of the exported file), and
    |trainer float forward - engine int| <= 2 cp on every position. Returns a dict with the counts."""
    net = v3.read_net(net_path)
    fens = [l.strip() for l in open(fens_path) if l.strip()]
    engine = [l.strip() for l in engine_lines if l.strip()]
    if len(engine) != len(fens):
        return {"pass": False, "error": f"{len(engine)} engine lines vs {len(fens)} FENs", "positions": 0}
    int_mism = 0
    float_bad = 0
    max_diff = 0.0
    sum_diff = 0.0
    bad_fens = 0
    examples = []
    codes_all = np.zeros((len(fens), 64), np.uint8)
    meta_all = np.zeros(len(fens), np.int64)
    for i, fen in enumerate(fens):
        codes_all[i], meta_all[i] = codes_from_fen(fen)
    us, them, ob = batch_features(codes_all, meta_all, cfg)
    with torch.no_grad():
        float_cp = model(torch.from_numpy(us), torch.from_numpy(them), torch.from_numpy(ob)).numpy().astype(np.float64)
    for i, fen in enumerate(fens):
        if engine[i] == "BADFEN":
            bad_fens += 1
            continue
        eng = int(engine[i].split()[0])
        cp, obk, _, _, _ = v3.evaluate(net, v3.board_from_fen(fen))
        if cp != eng:
            int_mism += 1
            if len(examples) < 5:
                examples.append(f"int mismatch line {i + 1}: engine {eng} trainer {cp} ({fen})")
        if obk != int(engine[i].split()[1]):
            int_mism += 1
        diff = abs(float_cp[i] - eng)
        max_diff = max(max_diff, diff)
        sum_diff += diff
        if diff > 2.0:
            float_bad += 1
            if len(examples) < 10:
                examples.append(f"float diff {diff:.3f} line {i + 1}: engine {eng} float {float_cp[i]:.3f} ({fen})")
    n = len(fens) - bad_fens
    return {"pass": int_mism == 0 and float_bad == 0 and n > 0, "positions": n, "badfen": bad_fens,
            "int_mismatches": int_mism, "float_over_2cp": float_bad, "max_abs_float_minus_int": round(max_diff, 4),
            "mean_abs_float_minus_int": round(sum_diff / max(n, 1), 4), "examples": examples}


def run_engine_eval(tool, net_path, fens_path):
    """forge_nnue_v3_tool eval <net> <fens>: stdout lines (one per FEN), stderr summary (fast-vs-reference)."""
    r = subprocess.run([tool, "eval", net_path, fens_path], capture_output=True, text=True)
    return r.returncode, r.stdout.splitlines(), r.stderr.strip().splitlines()[-1:]


# ---------------- train ----------------

def cmd_train(args):
    import glob
    import torch
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    cfg = make_cfg(args)
    os.makedirs(args.out, exist_ok=True)
    log = open(os.path.join(args.out, "log.txt"), "a", newline="\n")

    def say(msg):
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    say(f"config {json.dumps({k: v for k, v in cfg.items() if k not in ('king_map', 'output_map')}, sort_keys=True)}")
    say(f"args {json.dumps({k: v for k, v in vars(args).items() if k != 'func'}, sort_keys=True, default=str)}")
    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    model = build_model(cfg, torch)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    # run state that survives --resume
    tstate = {"step": 0, "seen": 0, "train_seconds": 0.0, "checkpoints": [], "best_exact": None, "best_step": None,
              "plateau": 0, "stop_reason": None, "chunks": 0}
    if args.resume:
        ck = torch.load(args.resume, map_location="cpu", weights_only=False)
        if ck["cfg"] != cfg:
            raise SystemExit("--resume: the checkpoint's model config differs from the command line")
        model.load_state_dict(ck["state"])
        opt.load_state_dict(ck["opt"])
        tstate = ck["train_state"]
        rng.bit_generator.state = ck["np_rng"]
        torch.set_rng_state(ck["torch_rng"])
        say(f"resumed {args.resume}: step {tstate['step']} seen {tstate['seen']} train_seconds {tstate['train_seconds']:.0f} "
            f"checkpoints {len(tstate['checkpoints'])} best_exact {tstate['best_exact']} plateau {tstate['plateau']}")
        if tstate["stop_reason"]:
            say(f"nothing to do: the run already stopped ({tstate['stop_reason']})")
            log.close()
            return
    tstate["chunks"] += 1
    stream = None
    data = None
    if args.pos_glob:
        pos_files = sorted(glob.glob(args.pos_glob))
        if args.exclude:
            pos_files = [f for f in pos_files if not any(x in os.path.basename(f) for x in args.exclude.split(","))]
        if not pos_files:
            raise SystemExit("no shards match --pos-glob")
        hce_files = [os.path.join(args.hce_dir, os.path.basename(f)[:-4] + ".hce") for f in pos_files] if args.hce_dir else [None] * len(pos_files)
        stream = ShardStream(pos_files, hce_files, args.chunk_rows, args.chunks, args.refresh_every, rng, bool(args.hce_dir), args.shard_weighting)
        say(f"stream: {len(pos_files)} shards ({sum(stream.rows_of)} rows), buffer {args.chunks} x {args.chunk_rows} rows, refresh every {args.refresh_every} batches, shard weighting {args.shard_weighting}; shards: {', '.join(os.path.basename(f) for f in pos_files)}")
        if cfg["residual"] and not args.hce_dir:
            raise SystemExit("--residual needs --hce-dir")
        train_n = None
        n = None
        val = 0
    else:
        data = read_fpos(args.pos, args.hce if args.residual or args.hce else None, args.max_rows)
        n = data["n"]
        val = min(args.val_rows, n // 10)
        train_n = n - val
        say(f"data {args.pos}: rows {n}, train {train_n}, val {val}, read {time.time() - t0:.1f}s")
        if cfg["residual"] and data["hce"] is None:
            raise SystemExit("--residual needs --hce")
    vdata = None
    if args.val_pos:
        vdata = read_fpos(args.val_pos, args.val_hce, args.val_max_rows)
        say(f"validation file {args.val_pos}: rows {vdata['n']}")
    exact_data = None
    if args.exact_pos:
        exact_data = read_fpos(args.exact_pos, args.exact_hce, args.exact_max_rows)
        say(f"exact holdout file {args.exact_pos}: rows {exact_data['n']}")
        if cfg["residual"] and exact_data["hce"] is None:
            raise SystemExit("--residual needs --exact-hce")

    def batch_tensors(rows):
        return tensors_from(data["codes"][rows], data["score"][rows], data["meta"][rows],
                            data["hce"][rows] if data["hce"] is not None else np.zeros(len(rows), np.int64), cfg, torch)

    def validate():
        model.eval()
        total, count = 0.0, 0
        with torch.no_grad():
            if vdata is not None:
                for start in range(0, vdata["n"], 8192):
                    rows = np.arange(start, min(start + 8192, vdata["n"]))
                    t = tensors_from(vdata["codes"][rows], vdata["score"][rows], vdata["meta"][rows],
                                     vdata["hce"][rows] if vdata["hce"] is not None else np.zeros(len(rows), np.int64), cfg, torch)
                    cp = model(t["us"], t["them"], t["ob"])
                    total += float(loss_fn(cp, t["score"], t["meta"], t["hce"], cfg, torch)) * len(rows)
                    count += len(rows)
            elif data is not None:
                for start in range(train_n, n, 8192):
                    rows = np.arange(start, min(start + 8192, n))
                    t = batch_tensors(rows)
                    cp = model(t["us"], t["them"], t["ob"])
                    total += float(loss_fn(cp, t["score"], t["meta"], t["hce"], cfg, torch)) * len(rows)
                    count += len(rows)
        model.train()
        return total / max(count, 1)

    def write_status():
        status = {k: v for k, v in tstate.items()}
        status["horizon_steps"] = args.steps
        status["out"] = args.out
        status["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        tmp = os.path.join(args.out, "status.json.tmp")
        with open(tmp, "w", newline="\n") as f:
            json.dump(status, f, indent=1, sort_keys=True)
        os.replace(tmp, os.path.join(args.out, "status.json"))

    def save_ckpt():
        path = os.path.join(args.out, "ckpt.pt")
        tmp = path + ".tmp"
        torch.save({"cfg": cfg, "state": model.state_dict(), "opt": opt.state_dict(), "train_state": tstate,
                    "np_rng": rng.bit_generator.state, "torch_rng": torch.get_rng_state(),
                    "args": {k: v for k, v in vars(args).items() if k != "func"}}, tmp)
        os.replace(tmp, path)

    def checkpoint(reason):
        """Export, exact holdout score (per phase), engine parity, stop decision; records everything in status.json."""
        idx = len(tstate["checkpoints"]) + 1
        step = tstate["step"]
        model.eval()
        prototype = bool(cfg.get("l2")) or bool(cfg.get("pairwise")) or bool(getattr(args, "float_exact", False))
        if prototype:
            # FB2-J7: no v3 file for prototype architectures; keep the float model and score it with the float forward
            net_path = os.path.join(args.out, f"ck{idx:02d}_step{step:07d}.pt")
            torch.save({"cfg": cfg, "state": model.state_dict(), "steps": step}, net_path)
            checksum, mw1, mb1, mw2 = 0, 0, 0, 0
        else:
            net_path = os.path.join(args.out, f"ck{idx:02d}_step{step:07d}.fnn3")
            checksum, mw1, mb1, mw2 = export_net(model, cfg, net_path, torch)
        entry = {"index": idx, "step": step, "seen": tstate["seen"], "train_seconds": round(tstate["train_seconds"], 1),
                 "net": os.path.basename(net_path), "checksum": f"{checksum:x}", "max_w1": mw1, "max_b1": mb1, "max_w2": mw2,
                 "lr": lr_at(step, args), "blend": blend_at(step, args), "reason": reason, "wall": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "metric": "float" if prototype else "exact"}
        t1 = time.time()
        if exact_data is not None:
            if prototype:
                ex = float_score(model, exact_data, cfg, torch)
            else:
                net = v3.read_net(net_path)
                ex = score_net_numpy(net, exact_data, net.residual, phases=True)
            entry.update({"exact_rows": exact_data["n"], "exact_b0.6": ex["mse_b0.6"], "exact_b0.8": ex["mse_b0.8"],
                          "exact_b1.0": ex["mse_b1.0"], "phase_rows": ex["phase_rows"], "phase_mse_b0.6": ex["phase_mse_b0.6"],
                          "exact_seconds": round(time.time() - t1, 1)})
        if args.parity_tool and args.parity_fens and not prototype:
            t2 = time.time()
            rc, lines, summary = run_engine_eval(args.parity_tool, net_path, args.parity_fens)
            par = parity_check(model, cfg, net_path, args.parity_fens, lines, torch)
            par["tool_rc"] = rc
            par["tool_summary"] = summary[0] if summary else ""
            par["seconds"] = round(time.time() - t2, 1)
            entry["parity"] = par
        model.train()
        # stop rules on the exact b0.6 loss
        if "exact_b0.6" in entry:
            cur = entry["exact_b0.6"]
            if tstate["best_exact"] is None or cur < tstate["best_exact"] - args.plateau_eps:
                tstate["best_exact"] = cur
                tstate["best_step"] = step
                tstate["plateau"] = 0
                shutil.copyfile(net_path, os.path.join(args.out, "best.pt" if prototype else "best.fnn3"))
                entry["best"] = True
            else:
                tstate["plateau"] += 1
                entry["best"] = False
            if args.target_loss and cur <= args.target_loss:
                tstate["stop_reason"] = f"target: exact b0.6 {cur:.6f} <= {args.target_loss}"
            elif args.plateau and tstate["plateau"] >= args.plateau:
                tstate["stop_reason"] = f"plateau: {tstate['plateau']} checkpoints without improving {tstate['best_exact']:.6f} (step {tstate['best_step']})"
        tstate["checkpoints"].append(entry)
        save_ckpt()
        write_status()
        par = entry.get("parity", {})
        say(f"ckpt {idx} step {step} seen {tstate['seen']} train_s {tstate['train_seconds']:.0f} lr {entry['lr']:.2e} blend {entry['blend']:.3f} "
            f"net {entry['net']} checksum {entry['checksum']} max|w1| {mw1} max|b1| {mb1} max|w2| {mw2}"
            + (f" exact_b0.6 {entry['exact_b0.6']:.6f} b0.8 {entry['exact_b0.8']:.6f} b1.0 {entry['exact_b1.0']:.6f} "
               f"phases {[round(x, 6) if x is not None else None for x in entry['phase_mse_b0.6']]} ({entry['exact_seconds']}s)" if "exact_b0.6" in entry else "")
            + (f" parity {'PASS' if par.get('pass') else 'FAIL'} int_mism {par.get('int_mismatches')} float>2cp {par.get('float_over_2cp')} "
               f"max {par.get('max_abs_float_minus_int')} tool_rc {par.get('tool_rc')} ({par.get('seconds')}s)" if par else "")
            + f" best {tstate['best_exact']} plateau {tstate['plateau']}"
            + (f" STOP {tstate['stop_reason']}" if tstate["stop_reason"] else ""))

    step = tstate["step"]
    seen = tstate["seen"]
    seen_start = seen
    train_seconds_base = float(tstate["train_seconds"])
    have_val = vdata is not None or val > 0
    if have_val and step == 0:
        say(f"step 0 val_loss {validate():.6f}")
    if args.ckpt_every_minutes and step == 0 and args.ckpt_at_start:
        checkpoint("start")
    t_start = time.time()
    last_report = t_start
    last_val = t_start
    last_ckpt = t_start
    while step < args.steps and not tstate["stop_reason"]:
        for g in opt.param_groups:
            g["lr"] = lr_at(step, args)
        blend = blend_at(step, args)
        if stream is not None:
            codes, score, meta, hce = stream.batch(args.batch)
            t = tensors_from(codes, score, meta, hce, cfg, torch)
        else:
            rows = rng.integers(0, train_n, size=args.batch)
            t = batch_tensors(rows)
        cp = model(t["us"], t["them"], t["ob"])
        loss = loss_fn(cp, t["score"], t["meta"], t["hce"], cfg, torch, blend)
        opt.zero_grad()
        loss.backward()
        opt.step()
        model.clip()
        step += 1
        seen += args.batch
        tstate["step"] = step
        tstate["seen"] = seen
        now = time.time()
        if now - last_report > 30 or step == args.steps or step == 1:
            elapsed = now - t_start
            say(f"step {step} seen {seen} loss {float(loss):.6f} lr {lr_at(step, args):.2e} blend {blend:.3f} elapsed {elapsed:.0f}s "
                f"pos/s {(seen - seen_start) / max(elapsed, 1e-9):.0f} total_train_s {train_seconds_base + elapsed:.0f}"
                + (f" chunks_loaded {stream.chunks_loaded}" if stream is not None else ""))
            last_report = now
        if args.export_every and step % args.export_every == 0 and step < args.steps:
            export_net(model, cfg, os.path.join(args.out, f"step{step:06d}.fnn3"), torch)
        if have_val and args.val_every_minutes and (now - last_val) / 60.0 >= args.val_every_minutes:
            say(f"step {step} val_loss {validate():.6f}")
            last_val = time.time()
        if args.ckpt_every_minutes and (now - last_ckpt) / 60.0 >= args.ckpt_every_minutes:
            tstate["train_seconds"] = train_seconds_base + (now - t_start)
            checkpoint("interval")
            paused_for = time.time() - now
            t_start += paused_for          # the checkpoint's own time does not count as training time
            last_ckpt = time.time()
            last_val = last_ckpt
        if args.max_minutes and (time.time() - t_start) / 60.0 >= args.max_minutes:
            say(f"pausing at step {step}: --max-minutes {args.max_minutes} reached (resume with --resume {os.path.join(args.out, 'ckpt.pt')})")
            break
    now = time.time()
    tstate["train_seconds"] = train_seconds_base + (now - t_start)
    if step >= args.steps and not tstate["stop_reason"]:
        tstate["stop_reason"] = f"horizon: {args.steps} steps"
    if args.ckpt_every_minutes:
        if tstate["stop_reason"] or args.ckpt_at_pause:
            checkpoint("final" if tstate["stop_reason"] else "pause")
        else:
            save_ckpt()
            write_status()
    if have_val:
        say(f"step {step} val_loss {validate():.6f}")
    torch.save({"cfg": cfg, "state": model.state_dict(), "steps": step}, os.path.join(args.out, "model.pt"))
    if cfg.get("l2") or cfg.get("pairwise"):
        say(f"saved {os.path.join(args.out, 'model.pt')} (prototype architecture, no v3 export) steps {step} seen {seen}"
            + (f" stop_reason {tstate['stop_reason']}" if tstate["stop_reason"] else " (paused)"))
    else:
        checksum, mw1, mb1, mw2 = export_net(model, cfg, os.path.join(args.out, "net.fnn3"), torch)
        say(f"exported {os.path.join(args.out, 'net.fnn3')} checksum {checksum:x} max|w1| {mw1} max|b1| {mb1} max|w2| {mw2} steps {step} seen {seen}"
            + (f" stop_reason {tstate['stop_reason']}" if tstate["stop_reason"] else " (paused)"))
    log.close()


def load_model(path, torch):
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    cfg = ckpt["cfg"]
    model = build_model(cfg, torch)
    model.load_state_dict(ckpt["state"])
    model.eval()
    return model, cfg


def cmd_export(args):
    import torch
    torch.set_num_threads(1)
    model, cfg = load_model(args.model, torch)
    checksum, mw1, mb1, mw2 = export_net(model, cfg, args.net, torch)
    print(f"exported {args.net} checksum {checksum:x} max|w1| {mw1} max|b1| {mb1} max|w2| {mw2}")


def cmd_parity(args):
    import torch
    torch.set_num_threads(1)
    model, cfg = load_model(args.model, torch)
    engine = [l for l in open(args.engine_out)]
    r = parity_check(model, cfg, args.net, args.fens, engine, torch)
    if "error" in r:
        print("FAIL: " + r["error"])
        sys.exit(1)
    print(f"positions {r['positions']} (badfen {r['badfen']}) int mismatches {r['int_mismatches']} float>2cp {r['float_over_2cp']} "
          f"max|float-int| {r['max_abs_float_minus_int']:.4f} mean {r['mean_abs_float_minus_int']:.4f}")
    for e in r["examples"]:
        print("  " + e)
    print("PASS" if r["pass"] else "FAIL")
    sys.exit(0 if r["pass"] else 1)


def cmd_score(args):
    net = v3.read_net(args.net)
    data = read_fpos(args.pos, args.hce, args.max_rows)
    result = score_net_numpy(net, data, net.residual, phases=args.phases)
    print(json.dumps({"net": args.net, "rows": data["n"], "residual": net.residual, **result}, sort_keys=True))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("--pos")
    t.add_argument("--hce")
    t.add_argument("--out", required=True)
    t.add_argument("--hidden", type=int, default=512)
    t.add_argument("--king-buckets", type=int, default=8)
    t.add_argument("--output-buckets", type=int, default=8)
    t.add_argument("--mirror", action="store_true")
    t.add_argument("--residual", action="store_true")
    t.add_argument("--no-factorizer", action="store_true")
    t.add_argument("--steps", type=int, default=100, help="schedule horizon (total steps of the whole run)")
    t.add_argument("--batch", type=int, default=4096)
    t.add_argument("--lr", type=float, default=1e-3)
    t.add_argument("--max-rows", type=int)
    t.add_argument("--val-rows", type=int, default=50000)
    t.add_argument("--seed", type=int, default=1)
    t.add_argument("--eval-scale", type=int, default=400)
    t.add_argument("--blend", type=float, default=0.6)
    t.add_argument("--init-scale", type=float, default=0.02)
    t.add_argument("--export-every", type=int, default=0)
    t.add_argument("--max-minutes", type=float, default=0.0, help="pause after this many minutes of this chunk (resumable)")
    t.add_argument("--threads", type=int, default=1)
    t.add_argument("--pos-glob", help="streaming mode: glob of FPOS shards (overrides --pos)")
    t.add_argument("--hce-dir", help="streaming mode: directory with the matching .hce files")
    t.add_argument("--exclude", default="", help="streaming mode: comma-separated substrings of shard names to skip (holdout)")
    t.add_argument("--chunk-rows", type=int, default=250000)
    t.add_argument("--chunks", type=int, default=8)
    t.add_argument("--refresh-every", type=int, default=25)
    t.add_argument("--shard-weighting", choices=["rows", "uniform"], default="rows",
                   help="streaming mode: pick shards proportional to their rows (default) or uniformly")
    t.add_argument("--val-pos", help="validation FPOS file for the quick torch validation")
    t.add_argument("--val-hce")
    t.add_argument("--val-max-rows", type=int, default=200000)
    t.add_argument("--val-every-minutes", type=float, default=10.0)
    t.add_argument("--lr-schedule", choices=["constant", "cosine", "linear"], default="constant")
    t.add_argument("--lr-final", type=float, default=5e-5)
    t.add_argument("--warmup-steps", type=int, default=0)
    t.add_argument("--blend-schedule", choices=["constant", "linear", "cosine"], default="constant")
    t.add_argument("--blend-start", type=float)
    t.add_argument("--blend-end", type=float)
    # FB2-J1: resumable checkpoints with exact scoring, parity and stop rules
    t.add_argument("--resume", help="ckpt.pt of a paused run (same model config and --out)")
    t.add_argument("--ckpt-every-minutes", type=float, default=0.0)
    t.add_argument("--ckpt-at-start", action="store_true", help="also checkpoint the untrained net (step 0)")
    t.add_argument("--ckpt-at-pause", action="store_true", help="full checkpoint (score + parity) when --max-minutes pauses the chunk")
    t.add_argument("--exact-pos", help="holdout FPOS file scored with the exact integer emulation at every checkpoint")
    t.add_argument("--exact-hce")
    t.add_argument("--exact-max-rows", type=int)
    t.add_argument("--parity-tool", help="forge_nnue_v3_tool executable (engine parity at every checkpoint)")
    t.add_argument("--parity-fens", help="FEN file for the parity check")
    t.add_argument("--target-loss", type=float, default=0.0, help="stop when the exact b0.6 holdout MSE is <= this")
    t.add_argument("--plateau", type=int, default=0, help="stop after this many checkpoints without a new best exact loss")
    t.add_argument("--plateau-eps", type=float, default=1e-5)
    # FB2-J7 v4 prototypes (trainer only; checkpoints keep .pt models and score the holdout with the float forward)
    t.add_argument("--l2", type=int, default=0, help="second layer width (2H -> L2 -> 1, clipped ReLU); 0 = the v3 single layer")
    t.add_argument("--pairwise", action="store_true", help="add a pairwise term sum(w3[ob] * screlu(us) * screlu(them))")
    t.add_argument("--float-exact", action="store_true", help="score the exact holdout with the float forward instead of the integer file (for prototype comparisons)")
    e = sub.add_parser("export")
    e.add_argument("--model", required=True)
    e.add_argument("--net", required=True)
    p = sub.add_parser("parity")
    p.add_argument("--model", required=True)
    p.add_argument("--net", required=True)
    p.add_argument("--fens", required=True)
    p.add_argument("--engine-out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--net", required=True)
    s.add_argument("--pos", required=True)
    s.add_argument("--hce")
    s.add_argument("--max-rows", type=int)
    s.add_argument("--phases", action="store_true")
    args = ap.parse_args()
    {"train": cmd_train, "export": cmd_export, "parity": cmd_parity, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    main()
