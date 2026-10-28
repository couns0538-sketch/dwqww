#!/usr/bin/env python3
# train_resid_v3.py: speed-only derivative of train_resid_v2.py (Forge trainer, AI-made for Couns). Changes: epoch-boundary prefetch overlap, packed H2D copy, loss-sync default 128. Same math.
# train_resid_v3b.py: RAM derivative of train_resid_v3a.py. --dev-scalars (per-step lr/blend/Adam factors as preallocated device tensors,
# filled by copy_, not new Python floats each step: suspected DirectML per-step host leak ~24 KB/step), int32 shuffle order in reused
# buffer(s), optional --mmap-data, private-memory logging + --max-ram-gb warning. Same order, same math (bit-identical on CPU).
# train_resid_v3c.py (S39, Opus 5.5 2026-10-27): derivative of train_resid_v3b.py (md5 b6758004). --epoch-positions N (default 0 = off):
# each epoch trains on N positions drawn with a seeded RNG from all training files, no repeats within an epoch, so steps/epoch and the
# lr/blend schedule stop growing with the data. --recent-weight W (default 1.0 = uniform): per-position weight of the last (newest) file of
# the sorted training file list, linear from 1.0 for the first. Off, or N >= train size: v3b exactly (same order, same math, same outputs).
# v3c + S50 (Opus 5.5 2026-10-27): --init-weights PATH (default off): warm start from a finished run's .pt, model weights only; optimizer,
# step, epoch, lr warmup/decay and blend ramp start fresh; the file's md5 goes to the settings dump and the checkpoint config. With
# --init-check the loaded net must reproduce the checkpoint's stored holdout val. With --resume the init file is not loaded.
# v3c + S-A2 clip (Opus 5.5 2026-10-27, trainer_v3c_clip.py): --weight-clip [C] (default off): after every optimizer step every
# exported tensor (W1, B1, W2, B2) is clamped to +-K/4096 with K = floor(C*4096) <= 32766; bare --weight-clip = K 21704, the largest
# K with 773*K < 2^24 (b1 + 768 inputs + 4 dirty columns per accumulator lane), so every export fits int16 with headroom and passes
# the engine's NnueInt16 check (exact float-grid, int32 accumulators >= 128x below overflow). Each export is verified (INT16 CHECK
# line; refused if a value exceeds K). Off: v3c exactly (same order, math, artifacts, stdout and settings dump).
"""Forge-768 residual NNUE trainer (GPU, DirectML/CPU). Own code, derived in structure from the
supplied train_nnue.py (md5 5A161C70...), but fed from pre-converted binaries:

  *.pos  (tools/fen2bin.cpp)  nibble boards + int16 teacher score (STM cp) + meta (stm, WHITE result)
  *.hce  (tools/hce_dump.cpp) int16 Forge-1ab50b2d evaluate_uncached (STM cp), line-aligned with .pos

Model/export are the same Forge net (768 -> H per perspective, SCReLU, 2H -> 1, int16 QAT, scale 4096).
--residual: logit = net(x) + K*hce/400, output layer starts at zero => first forward == HCE alone,
export writes FORGE_NNUE_RESIDUAL 1.  Loss = MSE(sigmoid(logit), blend*sigmoid(K*score/400) + (1-blend)*stm_result).
Holdout = whole files (never trained on).  Blend ramps linearly over training progress.
"""
from __future__ import annotations
import argparse, ctypes, glob, json, math, os, queue, sys, threading, time, uuid
from pathlib import Path
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

FEATURES = 768
SCALE = 4096.0
K_DEFAULT = 2.25
V3C_OFF = {"epoch_positions": 0, "recent_weight": 1.0, "init_weights": None,
           "weight_clip": 0.0}  # v3c options at their off values (not written to the settings dump)
INT16_MAX = 32767
CLIP_UNITS_DEFAULT = 21704  # S-A2: largest K with 773*K < 2**24 (lane bound |b1| + sum of 768 |w1| + 4*max|w1|)


# ----------------------------------------------------------------------------- data
def read_pos_header(path):
    with open(path, "rb") as f:
        h = f.read(16)
    if h[:4] != b"FPOS" or int.from_bytes(h[4:8], "little") != 1:
        raise ValueError(f"bad pos header {path}")
    return int.from_bytes(h[8:16], "little")


def load_set(pos_files, hce_dir, limit=None, need_hce=True):
    """Load pos(+hce) files into RAM, in the given order. limit = max positions (takes file prefixes)."""
    ns, picks = [], []
    total = 0
    for p in pos_files:
        n = read_pos_header(p)
        if limit is not None and total + n > limit:
            n_use = limit - total
        else:
            n_use = n
        if n_use <= 0:
            break
        picks.append((p, n, n_use))
        total += n_use
    boards = np.empty((total, 32), np.uint8)
    score = np.empty(total, np.int16)
    meta = np.empty(total, np.uint8)
    hce = np.empty(total, np.int16)
    o = 0
    for p, n, n_use in picks:
        b = np.memmap(p, np.uint8, "r", 16, (n, 32))
        s = np.memmap(p, np.int16, "r", 16 + n * 32, (n,))
        m = np.memmap(p, np.uint8, "r", 16 + n * 34, (n,))
        boards[o:o + n_use] = b[:n_use]; score[o:o + n_use] = s[:n_use]; meta[o:o + n_use] = m[:n_use]
        if (m[:n_use] == 255).any():
            raise ValueError(f"bad records in {p}")
        if need_hce:
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
    return dict(boards=boards, score=score, meta=meta, hce=hce, n=total, files=[(p, n_use) for p, n, n_use in picks])


class CatMap:
    """v3b --mmap-data: read-only view over per-file np.memmap arrays (concatenated in file order, file prefixes).
    __getitem__(idx) gathers rows for an int index array without loading the files into private memory."""
    def __init__(self, parts, offs, dtype, row_shape=()):
        self.parts, self.offs, self.dtype, self.row_shape = parts, np.asarray(offs, np.int64), dtype, row_shape

    def __getitem__(self, idx):
        idx = np.asarray(idx)
        out = np.empty((len(idx),) + self.row_shape, self.dtype)
        fid = np.searchsorted(self.offs, idx, side="right") - 1
        for f in np.unique(fid):
            sel = fid == f
            out[sel] = self.parts[f][idx[sel] - self.offs[f]]
        return out


def load_set_mmap(pos_files, hce_dir, limit=None):
    """v3b: same selection/validation as load_set, but arrays stay memory-mapped (file-backed pages, no private copy)."""
    picks, total = [], 0
    for p in pos_files:
        n = read_pos_header(p)
        n_use = limit - total if limit is not None and total + n > limit else n
        if n_use <= 0:
            break
        picks.append((p, n, n_use)); total += n_use
    B, S, M, H, offs, o = [], [], [], [], [], 0
    for p, n, n_use in picks:
        b = np.memmap(p, np.uint8, "r", 16, (n, 32))[:n_use]
        s = np.memmap(p, np.int16, "r", 16 + n * 32, (n,))[:n_use]
        m = np.memmap(p, np.uint8, "r", 16 + n * 34, (n,))[:n_use]
        if (m == 255).any():
            raise ValueError(f"bad records in {p}")
        hp = Path(hce_dir) / (Path(p).stem + ".hce")
        with open(hp, "rb") as f:
            h = f.read(16)
        if h[:4] != b"FHCE" or int.from_bytes(h[8:16], "little") != n:
            raise ValueError(f"hce header/count mismatch {hp} vs {p}")
        hh = np.memmap(hp, np.int16, "r", 16, (n,))[:n_use]
        if (hh == -32768).any():
            raise ValueError(f"bad hce in {hp}")
        B.append(b); S.append(s); M.append(m); H.append(hh); offs.append(o); o += n_use
    return dict(boards=CatMap(B, offs, np.uint8, (32,)), score=CatMap(S, offs, np.int16), meta=CatMap(M, offs, np.uint8),
                hce=CatMap(H, offs, np.int16), n=total, files=[(p, n_use) for p, n, n_use in picks])


# ----------------------------------------------------------------------------- memory (v3b)
def proc_mem_gb():
    """(process private GB, system available GB). Windows: PrivateUsage / ullAvailPhys; Linux: RssAnon / MemAvailable."""
    try:
        if os.name == "nt":
            class PMC(ctypes.Structure):
                _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [(f, ctypes.c_size_t) for f in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
            class MSX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [(f, ctypes.c_ulonglong) for f in (
                    "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
                    "ullAvailExtendedVirtual")]
            pmc = PMC(); pmc.cb = ctypes.sizeof(PMC)
            k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
            psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            k32.GetCurrentProcess.restype = ctypes.c_void_p
            psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
            ms = MSX(); ms.dwLength = ctypes.sizeof(MSX); k32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return pmc.PrivateUsage / 2**30, ms.ullAvailPhys / 2**30
        priv = avail = float("nan")
        for line in open("/proc/self/status"):
            if line.startswith("RssAnon:"):
                priv = int(line.split()[1]) / 2**20
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                avail = int(line.split()[1]) / 2**20
        return priv, avail
    except Exception:  # noqa  (logging only; never stops training)
        return float("nan"), float("nan")


def mem_report(tag, max_gb):
    priv, avail = proc_mem_gb()
    print(f"MEM {tag} trainer_private={priv:.2f}GB sys_avail={avail:.2f}GB", flush=True)
    if max_gb and priv == priv and priv > max_gb:
        print(f"WARNING: trainer private memory {priv:.2f}GB > --max-ram-gb {max_gb:g} (warning only; training continues)", flush=True)


def make_batch(d, idx):
    b = d["boards"][idx]
    codes = np.empty((len(idx), 64), np.uint8)
    codes[:, 0::2] = b & 15
    codes[:, 1::2] = b >> 4
    m = d["meta"][idx]
    return (codes, (m & 1), (m >> 1), d["score"][idx], d["hce"][idx])


PACK_W = 68  # v3: floats per position in the packed batch: 64 codes, stm, wres, score, hce_logit


def pack_batch(bt, k):
    """v3: one contiguous float32 buffer per batch (all values exact in float32; hce_logit computed exactly as v2's to_dev)."""
    codes, stm, wres, score, hce = bt
    B = len(codes)
    buf = np.empty(B * PACK_W, np.float32)
    buf[: B * 64] = codes.reshape(-1)
    buf[B * 64:B * 65] = stm
    buf[B * 65:B * 66] = wres
    buf[B * 66:B * 67] = score
    buf[B * 67:] = hce.astype(np.float32) * (k / 400.0)
    return buf


class Prefetcher:
    def __init__(self, d, order, batch, k, depth=6):
        self.q = queue.Queue(depth)
        self.d, self.order, self.batch, self.k = d, order, batch, k
        self.stop = threading.Event()
        self.t = threading.Thread(target=self.run, daemon=True)
        self.t.start()

    def _put(self, x):
        while not self.stop.is_set():
            try:
                self.q.put(x, timeout=0.1)
                return
            except queue.Full:
                pass

    def run(self):
        try:
            n = len(self.order)
            for i in range(0, n - self.batch + 1, self.batch):
                if self.stop.is_set():
                    return
                idx = np.sort(self.order[i:i + self.batch])
                self._put(pack_batch(make_batch(self.d, idx), self.k))
            self._put(None)
        except BaseException as e:  # noqa
            self._put(e)

    def close(self):
        """v3: stop the producer thread and join it (used on early exit / exceptions)."""
        self.stop.set()
        while self.t.is_alive():
            try:
                while True:
                    self.q.get_nowait()
            except queue.Empty:
                pass
            self.t.join(0.05)

    def __iter__(self):
        while True:
            x = self.q.get()
            if x is None:
                return
            if isinstance(x, BaseException):
                raise x
            yield x


def eval_order(n, batch):
    """Sequential order for evaluation incl. the tail (as full batches only; tail dropped is reported)."""
    return np.arange(n, dtype=np.int64)


# ----------------------------------------------------------------------------- fixed-size epochs (v3c)
def recent_weights(nfiles, w):
    """v3c --recent-weight: per-position weight of each training file in the trainer's file order (sorted paths, oldest first):
    linear from 1.0 (first file) to w (last file). w = 1.0 -> all 1.0."""
    if nfiles <= 1:
        return [1.0] * nfiles
    return [1.0 + (w - 1.0) * f / (nfiles - 1) for f in range(nfiles)]


def epoch_quotas(sizes, weights, total):
    """v3c: rows to draw from each file per epoch, proportional to rows * weight (largest remainder, ties -> lower file index),
    capped at the file's rows (the excess goes to the other files in proportion). sum == total. Exact rational arithmetic on the
    float weights (no rounding drift; same result on every platform)."""
    from fractions import Fraction
    if total < 0 or total > sum(sizes):
        raise ValueError(f"epoch positions {total} outside 0..{sum(sizes)}")
    weights = [Fraction(w) for w in weights]
    q = [0] * len(sizes)
    active = [f for f, n in enumerate(sizes) if n > 0]
    left = total
    while active and left:
        tot = sum(sizes[f] * weights[f] for f in active)
        capped = [f for f in active if left * sizes[f] * weights[f] >= sizes[f] * tot]  # share >= rows
        if not capped:
            share = {f: left * sizes[f] * weights[f] / tot for f in active}
            for f in active:
                q[f] = math.floor(share[f])
            for f in sorted(active, key=lambda f: (q[f] - share[f], f))[:left - sum(q[f] for f in active)]:
                q[f] += 1
            break
        for f in capped:
            q[f] = sizes[f]
            left -= sizes[f]
        active = [f for f in active if f not in capped]
    return q


def draw_weighted(buf, rng, offs, sizes, quotas, chunk=1 << 24):
    """v3c --recent-weight != 1: buf = arange(N) (rows in file order). Per file: shuffle its rows in place and keep the first quota
    rows (uniform draw without repeats inside the file), compacted to the front of buf; then shuffle buf[:sum(quotas)].
    In place: no array of size N is allocated (copies in chunks of <= 2**24 rows, like the arange fill). Returns sum(quotas)."""
    w = 0
    for o, n, q in zip(offs, sizes, quotas):
        seg = buf[o:o + n]
        if 0 < q < n:  # q == n keeps every row (order comes from the final shuffle); q == 0 keeps none
            rng.shuffle(seg)
        for i in range(0, q, chunk):  # destination starts at w <= o: never overwrites rows not yet copied
            j = min(q, i + chunk)
            buf[w + i:w + j] = seg[i:j]
        w += q
    rng.shuffle(buf[:w])
    return w


# ----------------------------------------------------------------------------- model
def features(codes, black):
    """codes [B,64] int64 (0 empty, 1..6 white PNBRQK, 7..12 black); black [B] int64 perspective colour.
    Returns [B,64] feature index (768 = empty) == forge::nnue::feature_index."""
    sq = torch.arange(64, device=codes.device).unsqueeze(0)
    c = codes - 1
    color = torch.div(c, 6, rounding_mode="floor")
    typ = c - color * 6
    bl = black.unsqueeze(1)
    rel = (color != bl).long()
    rsq = torch.where(bl == 1, sq ^ 56, sq.expand_as(codes))
    f = (rel * 6 + typ) * 64 + rsq
    return torch.where(codes > 0, f, torch.full_like(f, FEATURES))


def dense(codes, black):
    f = features(codes, black)
    x = torch.zeros(codes.shape[0], FEATURES + 1, device=codes.device).scatter_(1, f, 1.0)
    return x[:, :FEATURES]


class NNUE(nn.Module):
    def __init__(self, hidden, qat=True, residual=True):
        super().__init__()
        self.hidden, self.qat, self.residual = hidden, qat, residual
        self.ft = nn.Linear(FEATURES, hidden)
        self.out = nn.Linear(2 * hidden, 1)
        nn.init.normal_(self.ft.weight, std=0.02)
        nn.init.zeros_(self.ft.bias)
        nn.init.zeros_(self.out.bias)
        if residual:
            nn.init.zeros_(self.out.weight)  # first forward == HCE alone

    def q(self, p):
        if not self.qat:
            return p
        scaled = p * SCALE
        rounded = torch.sign(scaled) * torch.floor(torch.abs(scaled) + 0.5)
        qv = torch.clamp(rounded, -32767, 32767) / SCALE
        return p + (qv - p).detach()

    def forward(self, codes, stm, hce_logit):
        xs = dense(codes, stm)
        xo = dense(codes, 1 - stm)
        w, b = self.q(self.ft.weight), self.q(self.ft.bias)
        hs = torch.clamp(F.linear(xs, w, b), 0.0, 1.0).square()
        ho = torch.clamp(F.linear(xo, w, b), 0.0, 1.0).square()
        out = F.linear(torch.cat([hs, ho], 1), self.q(self.out.weight), self.q(self.out.bias)).squeeze(1)
        return out + hce_logit if self.residual else out

    @torch.no_grad()
    def project_weights(self):
        for p in self.parameters():
            p.clamp_(-32767 / SCALE, 32767 / SCALE)

    @torch.no_grad()
    def clip_weights(self, units):
        """S-A2 --weight-clip: clamp every parameter (W1, B1, W2, B2) to +-units/4096 (exact in float32)."""
        bound = units / SCALE
        for p in self.parameters():
            p.clamp_(-bound, bound)


def targets(score_t, stm_t, wres_t, k, blend):
    """score int16 STM cp, wres = white result*2 (0,1,2). Returns teacher, stm_result, blended target."""
    teacher = torch.sigmoid(torch.clamp(score_t * (k / 400.0), -40, 40))
    white = wres_t * 0.5
    stm_res = torch.where(stm_t == 0, white, 1.0 - white)
    return teacher, stm_res, blend * teacher + (1.0 - blend) * stm_res


def targets_t(score_t, stm_t, wres_t, k, blend_t, omb_t):
    """v3b: targets() with blend and (1-blend) as 0-dim float32 device tensors (same float32 values as the Python scalars)."""
    teacher = torch.sigmoid(torch.clamp(score_t * (k / 400.0), -40, 40))
    white = wres_t * 0.5
    stm_res = torch.where(stm_t == 0, white, 1.0 - white)
    return teacher, stm_res, blend_t * teacher + omb_t * stm_res


def to_dev(buf, dev, k):
    """v3: buf = pack_batch(...); ONE host->device copy, then device-side slices (same dtypes/values as v2)."""
    B = buf.size // PACK_W
    t = torch.from_numpy(buf).to(dev)
    codes = t[: B * 64].view(B, 64).long()
    stm = t[B * 64:B * 65].long()
    wres = t[B * 65:B * 66]
    score = t[B * 66:B * 67]
    hce_l = t[B * 67:]
    return codes, stm, wres, score, hce_l


class EpochPrep:
    """v3: builds one epoch's training order + Prefetcher in a background thread (overlaps the epoch boundary)."""
    def __init__(self, fn, ep, wait=None):
        self.res, self.err = None, None
        self.t = threading.Thread(target=self._run, args=(fn, ep, wait), daemon=True)
        self.t.start()

    def _run(self, fn, ep, wait):
        try:
            if wait is not None:  # v3b: reused order buffer -> wait until the previous producer has read all of it
                wait.t.join()
            self.res = fn(ep)
        except BaseException as e:  # noqa
            self.err = e

    def get(self):
        self.t.join()
        if self.err is not None:
            raise self.err
        res, self.res = self.res, None
        return res

    def close(self):
        self.t.join()
        if self.res is not None:
            self.res.close()
            self.res = None


@torch.no_grad()
def evaluate(model, d, idx_all, dev, k, batch, blends=(1.0, 0.6), baseline=False, limit_batches=None):
    """MSE on positions idx_all. Returns dict blend -> mse. baseline=True ignores the net (HCE alone)."""
    sums = {b: 0.0 for b in blends}
    cnt = 0
    model.eval()
    nb = len(idx_all) // batch
    if limit_batches:
        nb = min(nb, limit_batches)
    pf = Prefetcher(d, idx_all[: nb * batch], batch, k)
    for bt in pf:
        codes, stm, wres, score, hce_l = to_dev(bt, dev, k)
        logit = hce_l if baseline else model(codes, stm, hce_l)
        pred = torch.sigmoid(logit)
        for b in blends:
            _, _, tg = targets(score, stm, wres, k, b)
            sums[b] += float(F.mse_loss(pred, tg, reduction="sum").cpu())
        cnt += len(codes)
    model.train()
    return {b: sums[b] / max(cnt, 1) for b in blends}, cnt


# ----------------------------------------------------------------------------- export
def atomic_write(path, write):
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with open(temp, "xb") as dst:
            write(dst)
            dst.flush()
            os.fsync(dst.fileno())
        if path.exists():
            raise FileExistsError(str(path))
        os.rename(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def int16_check(quant, units):
    """S-A2: the exported int16 tensors (W1 as [768*H] input-major, B1, W2, B2) against the clip bound `units`.
    Returns the INT16 CHECK report; raises if any value exceeds the bound (or touches the int16 rail)."""
    w1, b1, w2, b2 = (q.astype(np.int64) for q in quant)
    hidden = len(b1)
    a1 = np.abs(w1).reshape(768, hidden)
    lane = int((np.abs(b1) + a1.sum(axis=0)).max() + 4 * a1.max())
    names = ("W1", "B1", "W2", "B2")
    report = {"units": units, "bound": units / SCALE,
              "max_abs": {n: int(np.abs(q).max()) for n, q in zip(names, (w1, b1, w2, b2))},
              "at_bound": {n: int((np.abs(q) == units).sum()) for n, q in zip(names, (w1, b1, w2, b2))},
              "at_int16_rail": int(sum((np.abs(q) >= INT16_MAX).sum() for q in (w1, b1, w2, b2))),
              "lane_bound": lane, "lane_bound_below_2^24": lane < (1 << 24), "int32_headroom": (2**31 - 1) // max(lane, 1)}
    bad = [n for n in names if report["max_abs"][n] > units]
    if bad:  # units <= 32766, so a value at the int16 rail also lands here
        raise ValueError(f"INT16 CHECK FAILED: {bad} exceed the clip bound {units}: {report}")
    return report


def export_forge(model, stem, k, residual, clip_units=0):
    hidden = model.hidden
    arrays = [model.ft.weight.detach().cpu().t().contiguous().numpy().ravel(),
              model.ft.bias.detach().cpu().numpy(),
              model.out.weight.detach().cpu().numpy().ravel(),
              model.out.bias.detach().cpu().numpy()]
    if not all(np.isfinite(v).all() for v in arrays):
        raise RuntimeError("Non-finite parameters; refusing to export")
    quant = []
    for v in arrays:
        sc = v.astype(np.float64) * SCALE
        r = np.sign(sc) * np.floor(np.abs(sc) + 0.5)
        if (np.abs(r) > 32767).any():
            raise ValueError("Weights exceed int16 range")
        quant.append(r.astype(np.int16))
    clip_report = int16_check(quant, clip_units) if clip_units else None  # S-A2 --weight-clip: verified before any file is written
    lines = ["// Generated by train_resid.py; Forge-768 network.",
             "#include <cstdint>", f"#define FORGE_NNUE_RESIDUAL {1 if residual else 0}",
             f"static_assert(forge::nnue::InputCount == 768 && forge::nnue::HiddenSize == {hidden},",
             '              "NNUE shape mismatch; rebuild with the correct FORGE_NNUE_HIDDEN");',
             'static_assert(forge::nnue::SigmoidK == 2.25F, "NNUE output scale mismatch");',
             'static_assert(forge::nnue::WeightScale == 4096.0F && forge::nnue::OutputScale == 4096.0F,',
             '              "NNUE quantization scale mismatch");']
    for name, v in zip(("NnueW1", "NnueB1", "NnueW2"), quant[:3]):
        lines.append(f"static const std::int16_t {name}[{len(v)}] = {{")
        lines.extend("  " + ", ".join(map(str, v[i:i + 24])) + "," for i in range(0, len(v), 24))
        lines.append("};")
    lines.append(f"static const std::int16_t NnueB2 = {int(quant[3][0])};")
    atomic_write(stem.with_suffix(".inc"), lambda dst: dst.write(("\n".join(lines) + "\n").encode("ascii")))
    raw = b"".join(np.asarray(v, dtype="<f4").tobytes() for v in arrays)
    atomic_write(stem.with_suffix(".bin"), lambda dst: dst.write(raw))
    return clip_report


def cpu_copy(v):
    if torch.is_tensor(v):
        return v.detach().cpu().clone()
    if isinstance(v, dict):
        return {a: cpu_copy(b) for a, b in v.items()}
    if isinstance(v, list):
        return [cpu_copy(b) for b in v]
    return v


def device_for(name, index=None, requested="7900 XT"):
    if name == "cpu":
        return torch.device("cpu")
    import torch_directml
    names = [torch_directml.device_name(i) for i in range(torch_directml.device_count())]
    if index is None:
        m = [i for i, n in enumerate(names) if requested.lower() in n.lower()]
        if not m:
            raise ValueError(f"GPU {requested!r} not found: {names}")
        index = m[0]
    print(f"DirectML GPU {index}: {names[index]}", flush=True)
    return torch_directml.device(index)


# ----------------------------------------------------------------------------- warm start (v3c, S50)
def file_md5(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_init_weights(model, path, hidden, residual, qat):
    """v3c --init-weights: copy the model weights (only) of a trainer checkpoint (.pt payload with 'model', or a bare state_dict)
    into model. Optimizer state, step and epoch are not taken. Refuses another hidden size / residual mode (and any shape mismatch,
    via strict load_state_dict) and non-finite weights. Returns {'val': the checkpoint's holdout val by blend or None, 'info': text}."""
    ck = torch.load(path, map_location="cpu", weights_only=True)
    payload = isinstance(ck, dict) and "model" in ck
    sd = ck["model"] if payload else ck
    cfg = ck.get("config", {}) if payload else {}
    for key, want in (("hidden", hidden), ("residual", residual)):
        if key in cfg and cfg[key] != want:
            raise ValueError(f"--init-weights {path}: checkpoint {key}={cfg[key]} but this run has {key}={want}")
    if "qat" in cfg and cfg["qat"] != qat:
        print(f"WARNING: --init-weights checkpoint qat={cfg['qat']} but this run has qat={qat}", flush=True)
    if not all(torch.isfinite(v).all() for v in sd.values()):
        raise ValueError(f"--init-weights {path}: non-finite weights")
    model.load_state_dict(sd)
    val = ck.get("val") if payload else None
    info = (f"checkpoint hidden={cfg.get('hidden')} residual={cfg.get('residual')} next_epoch={ck.get('next_epoch')} step={ck.get('step')}"
            if payload else "bare state_dict")
    return {"val": {float(b): float(v) for b, v in val.items()} if val else None, "info": info}


# ----------------------------------------------------------------------------- main
def expand(patterns):
    out = []
    for p in patterns:
        out.extend(sorted(glob.glob(p)))
    return sorted(set(out))


def make_adam_devscalars(base):
    """v3b: AdamDML step with the per-step factors (-lr/bc1 and bc2s) in a preallocated 2-float device tensor updated by
    copy_. Same float32 values and op order as AdamDML on CPU: addcdiv_ computes self + (value * t1) / t2, here
    p.add_((m * ns) / denom); v.sqrt() / bc2s with bc2s as a 0-dim float32 tensor. State/state_dict format unchanged."""
    class AdamDMLDevScalars(base):
        def __init__(self, params, dev=None, **kw):
            super().__init__(params, **kw)
            self._sc = torch.zeros(2, device=dev)  # [-lr/bc1, bc2s]
            self._ns, self._bc2s = self._sc[0], self._sc[1]

        @torch.no_grad()
        def step(self, closure=None):
            assert closure is None
            for g in self.param_groups:
                b1, b2 = g["betas"]; lr = g["lr"]; eps = g["eps"]
                ps = [p for p in g["params"] if p.grad is not None]
                if not ps:
                    continue
                for p in ps:
                    st = self.state[p]
                    if len(st) == 0:
                        st["step"] = torch.tensor(0.0)
                        st["exp_avg"] = torch.zeros_like(p, memory_format=torch.preserve_format)
                        st["exp_avg_sq"] = torch.zeros_like(p, memory_format=torch.preserve_format)
                    st["step"] += 1
                ts = {float(self.state[p]["step"]) for p in ps}
                assert len(ts) == 1, "AdamDMLDevScalars: params of one group must share the step count"
                t = ts.pop()
                bc1 = 1 - b1 ** t; bc2s = math.sqrt(1 - b2 ** t)
                self._sc.copy_(torch.tensor([-lr / bc1, bc2s], dtype=torch.float32))
                for p in ps:
                    st = self.state[p]
                    m, v, gr = st["exp_avg"], st["exp_avg_sq"], p.grad
                    m.mul_(b1).add_(gr, alpha=1 - b1)
                    v.mul_(b2).addcmul_(gr, gr, value=1 - b2)
                    denom = (v.sqrt() / self._bc2s).add_(eps)
                    p.add_(torch.mul(m, self._ns).div_(denom))
            return None
    return AdamDMLDevScalars


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train", nargs="+", help="train .pos files/globs (hce files expected in --hce-dir)")
    ap.add_argument("--holdout", nargs="+", required=True, help="holdout .pos files (whole files)")
    ap.add_argument("--hce-dir", required=True)
    ap.add_argument("--device", choices=["directml", "cpu"], default="directml")
    ap.add_argument("--device-index", type=int)
    ap.add_argument("--shape", type=int, default=128, help="hidden width H")
    ap.add_argument("--residual", action="store_true")
    ap.add_argument("--baseline-only", action="store_true", help="report HCE-alone loss on the holdout and exit")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=4096)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--min-lr-frac", type=float, default=0.01)
    ap.add_argument("--warmup-steps", type=int, default=300)
    ap.add_argument("--blend-start", type=float, default=1.0)
    ap.add_argument("--blend-end", type=float, default=0.6)
    ap.add_argument("--sigmoid-k", type=float, default=K_DEFAULT)
    ap.add_argument("--no-qat", action="store_true")
    ap.add_argument("--max-train", type=int, default=0, help="limit training positions (file prefixes); 0 = all")
    ap.add_argument("--val-positions", type=int, default=4_000_000, help="fixed random holdout subset per epoch (0 = all)")
    ap.add_argument("--final-full-val", action="store_true")
    ap.add_argument("--steps-per-epoch", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--run-dir", default="forge-resid-run")
    ap.add_argument("--resume")
    ap.add_argument("--log-every", type=float, default=30.0)
    ap.add_argument("--adam-impl", choices=["dml", "torch"], default="dml", help="dml = Adam without lerp_ (same math, runs on DirectML); torch = stock")
    ap.add_argument("--loss-sync-every", type=int, default=128, help="read the training loss back to the CPU every N steps (1 = old behaviour)")
    ap.add_argument("--init-check", action="store_true", help="assert residual init val == baseline val")
    ap.add_argument("--guard-tag", help="ignored; lets gpu_guard v3 (matches train_resid_v2.py) see this trainer")
    ap.add_argument("--dev-scalars", type=int, choices=[0, 1], default=1, help="v3b: per-step lr/blend/Adam factors as device tensors updated by copy_ (1, default) or Python floats as v3a (0)")
    ap.add_argument("--order-buffers", type=int, choices=[1, 2], default=1, help="v3b: int32 shuffle buffers; 1 = one reused buffer (next order built after the producer finished), 2 = ping-pong (full overlap)")
    ap.add_argument("--mmap-data", action="store_true", help="v3b: keep the train set memory-mapped instead of loading it (off by default)")
    ap.add_argument("--max-ram-gb", type=float, default=0.0, help="v3b: print a WARNING when trainer private memory exceeds this (0 = off); never stops")
    ap.add_argument("--epoch-positions", type=int, default=0, help="v3c: each epoch trains on N positions drawn with a seeded RNG from all training files, no repeats within an epoch (0 = off: full epochs as v3b; N >= train size: full epochs)")
    ap.add_argument("--recent-weight", type=float, default=1.0, help="v3c: with --epoch-positions, per-position weight of the last file of the sorted training file list (linear from 1.0 for the first file); 1.0 = uniform (default)")
    ap.add_argument("--init-weights", help="v3c: warm start: model weights (only) from a finished run's .pt (trainer checkpoint or bare state_dict); optimizer, lr warmup/decay and blend ramp start fresh; md5 logged in the settings dump (default off; not loaded with --resume)")
    ap.add_argument("--weight-clip", type=float, nargs="?", const=CLIP_UNITS_DEFAULT / SCALE, default=0.0, metavar="C",
                    help=f"S-A2: clamp W1, B1, W2, B2 to +-K/4096, K = floor(C*4096) in 1..32766, after every optimizer step and verify "
                         f"every export (INT16 CHECK); bare --weight-clip = K {CLIP_UNITS_DEFAULT} (C {CLIP_UNITS_DEFAULT / SCALE}): 773*K < 2^24, "
                         "so the export passes the engine's NnueInt16 check (default 0 = off)")
    a = ap.parse_args()
    clip_units = 0  # S-A2 --weight-clip in int units of 1/4096 (0 = off)
    if a.weight_clip != 0.0:
        if not math.isfinite(a.weight_clip) or not 1 <= math.floor(a.weight_clip * SCALE) <= INT16_MAX - 1:
            ap.error(f"--weight-clip C needs 1 <= floor(C*4096) <= {INT16_MAX - 1} (C in [{1 / SCALE}, {(INT16_MAX - 1) / SCALE}])")
        clip_units = math.floor(a.weight_clip * SCALE)
    if a.epoch_positions < 0 or 0 < a.epoch_positions < a.batch_size:
        ap.error("--epoch-positions must be 0 (off) or at least one batch")
    if not (math.isfinite(a.recent_weight) and a.recent_weight > 0):
        ap.error("--recent-weight must be a positive number")
    if a.recent_weight != 1.0 and not a.epoch_positions:
        ap.error("--recent-weight needs --epoch-positions")
    init_md5 = None  # v3c --init-weights: hashed before the run dir exists (a missing file leaves no run dir behind)
    if a.init_weights:
        if os.path.isfile(a.init_weights):
            init_md5 = file_md5(a.init_weights)
        elif a.resume:
            init_md5 = "missing"  # a resumed warm start restores model + optimizer from --resume; the init file is not needed
        else:
            ap.error(f"--init-weights {a.init_weights}: no such file")
    k = a.sigmoid_k
    if k != K_DEFAULT:
        print("WARNING: export needs sigmoid-k 2.25", flush=True)
    torch.manual_seed(a.seed)
    dev = device_for(a.device, a.device_index)
    run = Path(a.run_dir)
    run.mkdir(parents=True, exist_ok=bool(a.resume) or a.baseline_only)
    settings = {key: v for key, v in vars(a).items() if not (key in V3C_OFF and v == V3C_OFF[key])}  # v3c: off -> v3b's dump
    if init_md5:
        settings["init_weights_md5"] = init_md5
    (run / f"settings_{int(time.time())}.txt").write_text(" ".join(sys.argv) + "\n" + json.dumps(settings, indent=1))
    t0 = time.time()
    hold_files = expand(a.holdout)
    hold = load_set(hold_files, a.hce_dir)
    print(f"holdout: {hold['n']:,} positions from {len(hold_files)} files ({time.time() - t0:.0f}s)", flush=True)
    rng = np.random.default_rng(12345)
    if a.val_positions and a.val_positions < hold["n"]:
        val_idx = np.sort(rng.choice(hold["n"], a.val_positions, replace=False))
    else:
        val_idx = np.arange(hold["n"], dtype=np.int64)
    full_idx = np.arange(hold["n"], dtype=np.int64)
    model = NNUE(a.shape, qat=not a.no_qat, residual=a.residual or a.baseline_only).to(dev)
    base_sub, nb = evaluate(model, hold, val_idx, dev, k, a.batch_size, baseline=True)
    print(f"BASELINE HCE-alone holdout subset n={nb:,}: mse_teacher(blend1.0)={base_sub[1.0]:.6f} mse_blend0.6={base_sub[0.6]:.6f}", flush=True)
    if a.baseline_only:
        full, nf = evaluate(model, hold, full_idx, dev, k, a.batch_size, baseline=True)
        print(f"BASELINE HCE-alone holdout FULL n={nf:,}: mse_teacher={full[1.0]:.6f} mse_blend0.6={full[0.6]:.6f}", flush=True)
        # extra blends for reference
        ex, _ = evaluate(model, hold, full_idx, dev, k, a.batch_size, blends=(0.0, 0.4, 0.8), baseline=True)
        print("BASELINE extra blends full: " + " ".join(f"b{b}={v:.6f}" for b, v in ex.items()), flush=True)
        return 0
    warm = None  # v3c --init-weights
    if a.init_weights and a.resume:
        print(f"init-weights {a.init_weights} (md5 {init_md5}): not loaded, --resume restores model and optimizer", flush=True)
    elif a.init_weights:
        warm = load_init_weights(model, a.init_weights, a.shape, bool(a.residual), not a.no_qat)
        print(f"init-weights: model weights from {a.init_weights} (md5 {init_md5}; {warm['info']}); optimizer, lr and blend schedules "
              "start fresh", flush=True)
    if a.init_check and warm is not None:  # v3c warm start: the loaded net must reproduce its checkpoint's holdout val
        init, _ = evaluate(model, hold, val_idx, dev, k, a.batch_size)
        ref = warm["val"]
        if ref is None:
            print(f"INIT warm-start net: mse_teacher={init[1.0]:.6f} mse_b0.6={init[0.6]:.6f} (checkpoint has no val: check skipped)", flush=True)
        else:
            print(f"INIT warm-start net: mse_teacher={init[1.0]:.6f} mse_b0.6={init[0.6]:.6f} (checkpoint val {ref[1.0]:.6f}/{ref[0.6]:.6f})", flush=True)
            if abs(init[1.0] - ref[1.0]) > 1e-6 or abs(init[0.6] - ref[0.6]) > 1e-6:
                print("INIT CHECK FAILED (warm start != checkpoint val; the source run's --holdout and --val-positions are needed)", flush=True)
                return 3
            print("INIT CHECK OK (warm start == checkpoint val)", flush=True)
    elif a.init_check:
        init, _ = evaluate(model, hold, val_idx, dev, k, a.batch_size)
        print(f"INIT residual net: mse_teacher={init[1.0]:.6f} mse_b0.6={init[0.6]:.6f} (baseline {base_sub[1.0]:.6f}/{base_sub[0.6]:.6f})", flush=True)
        if abs(init[1.0] - base_sub[1.0]) > 1e-6 or abs(init[0.6] - base_sub[0.6]) > 1e-6:
            print("INIT CHECK FAILED", flush=True)
            return 3
        print("INIT CHECK OK (residual init == HCE alone)", flush=True)
    train_files = expand(a.train)
    train_files = [f for f in train_files if f not in hold_files]
    t1 = time.time()
    train = (load_set_mmap if a.mmap_data else load_set)(train_files, a.hce_dir, limit=a.max_train or None)
    N = train["n"]
    print(f"train: {N:,} positions from {len(train['files'])} files ({time.time() - t1:.0f}s load)", flush=True)
    E = a.epoch_positions if a.epoch_positions < N else 0  # v3c: E > 0 = fixed-size epochs; 0 = full epochs (v3b)
    sizes = offs = quotas = None  # v3c: per-file draw plan, only with --recent-weight != 1
    if a.epoch_positions and not E:
        print(f"epoch-positions {a.epoch_positions:,} >= train {N:,}: full epochs (v3b order"
              f"{'; recent-weight has no effect' if a.recent_weight != 1.0 else ''})", flush=True)
    elif E:
        print(f"epoch-positions: {E:,} of {N:,} train positions per epoch (seeded draw, no repeats within an epoch), recent-weight {a.recent_weight:g}", flush=True)
        if a.recent_weight != 1.0:
            sizes = [n for _, n in train["files"]]
            offs = [int(o) for o in np.cumsum([0] + sizes[:-1])]
            weights = recent_weights(len(sizes), a.recent_weight)
            quotas = epoch_quotas(sizes, weights, E)
            print("epoch-positions per file (weight drawn/rows): " + ", ".join(
                f"{Path(p).name} {w:.4f} {q:,}/{n:,}" for (p, n), w, q in zip(train["files"], weights, quotas)), flush=True)
    spe = (E or N) // a.batch_size
    if a.steps_per_epoch:
        spe = min(spe, a.steps_per_epoch)
    total_steps = spe * a.epochs
    if a.adam_impl == "dml":  # QA util 2026-10-24: stock Adam's lerp_ has no DirectML kernel -> CPU round trip every step
        sys.path.insert(0, str(Path(__file__).resolve().parent)); from qa_adam_dml import AdamDML
        if a.dev_scalars:
            opt = make_adam_devscalars(AdamDML)(model.parameters(), lr=a.lr, foreach=False, dev=dev)
        else:
            opt = AdamDML(model.parameters(), lr=a.lr, foreach=False)
    else:
        opt = torch.optim.Adam(model.parameters(), lr=a.lr, foreach=False)
    print(f"optimizer: {type(opt).__name__} (--adam-impl {a.adam_impl}), loss sync every {a.loss_sync_every} steps", flush=True)
    if a.dev_scalars and a.adam_impl != "dml":
        print("WARNING: --dev-scalars covers blend only with --adam-impl torch (stock Adam keeps Python-float lr)", flush=True)
    mem_report("after-load", a.max_ram_gb)
    start_epoch, step = 0, 0
    if a.resume:
        ck = torch.load(a.resume, map_location="cpu", weights_only=True)
        model.load_state_dict(ck["model"]); opt.load_state_dict(ck["optimizer"])
        start_epoch, step = ck["next_epoch"], ck["step"]
        print(f"resumed {a.resume}: next_epoch={start_epoch} step={step}", flush=True)
    config = {"hidden": a.shape, "residual": bool(a.residual), "qat": not a.no_qat, "sigmoid_k": k,
              "features": "forge768-relative-pieces-rank-flip", "epochs": a.epochs, "steps_per_epoch": spe}
    if E:  # v3c: recorded only when fixed-size epochs are active (off -> v3b's config, .json and .pt)
        config["epoch_positions"] = E
        config["recent_weight"] = a.recent_weight
    if init_md5:  # v3c: warm-start provenance (kept by resumed epochs)
        config["init_weights_md5"] = init_md5
    if clip_units:  # S-A2: recorded only when the clip is on (off -> v3c's config, .json and .pt)
        config["weight_clip_units"] = clip_units
        print(f"weight-clip: W1 B1 W2 B2 clamped to +-{clip_units}/4096 = +-{clip_units / SCALE:.9g} after every step "
              f"(int16 rail {INT16_MAX}; accumulator lane bound <= 773*{clip_units} = {773 * clip_units:,} "
              f"{'<' if 773 * clip_units < (1 << 24) else '>='} 2^24)", flush=True)

    def lr_at(s):
        if s < a.warmup_steps:
            return a.lr * (s + 1) / a.warmup_steps
        pr = (s - a.warmup_steps) / max(1, total_steps - a.warmup_steps)
        return a.lr * (a.min_lr_frac + (1 - a.min_lr_frac) * 0.5 * (1 + math.cos(math.pi * min(pr, 1.0))))

    def blend_at(s):
        pr = min(1.0, s / max(1, total_steps - 1))
        return a.blend_start + (a.blend_end - a.blend_start) * pr

    print(f"steps/epoch={spe:,} total={total_steps:,} batch={a.batch_size} lr={a.lr} cosine blend {a.blend_start}->{a.blend_end}", flush=True)
    tstart = time.time(); last = tstart; seen = 0; ls = 0.0

    # v3b: int32 order in reused buffer(s). Generator.shuffle(arange(N) int32) == Generator.permutation(N) (same draws;
    # checked equal for N = 1e3, 32e6, 137,381,087). Needs N < 2**31.
    if N >= 2**31:
        raise ValueError("int32 order needs N < 2**31")
    order_bufs = [np.empty(N, np.int32) for _ in range(a.order_buffers)]

    def epoch_feed(e):
        buf = order_bufs[e % len(order_bufs)]
        for i in range(0, N, 1 << 24):  # in-place arange, no int64 temp of size N
            buf[i:i + (1 << 24)] = np.arange(i, min(N, i + (1 << 24)), dtype=np.int32)
        rng_e = np.random.default_rng(a.seed * 1000 + e)
        if quotas is None:  # v3b order; a v3c fixed-size epoch (uniform) trains on its first E entries
            rng_e.shuffle(buf)
        else:  # v3c --recent-weight: per-file draws without repeats, compacted and shuffled into buf[:E]
            draw_weighted(buf, rng_e, offs, sizes, quotas)
        return Prefetcher(train, buf[: spe * a.batch_size], a.batch_size, k)

    sc_dev = torch.zeros(2, device=dev) if a.dev_scalars else None  # [blend, 1-blend]
    blend_t, omb_t = (sc_dev[0], sc_dev[1]) if a.dev_scalars else (None, None)
    nxt = EpochPrep(epoch_feed, start_epoch) if start_epoch < a.epochs else None
    pf = None
    try:
      for ep in range(start_epoch, a.epochs):
        pf = nxt.get(); nxt = None
        if ep + 1 < a.epochs:  # v3: next epoch's permutation + prefetcher build while this epoch trains
            nxt = EpochPrep(epoch_feed, ep + 1, wait=pf if len(order_bufs) == 1 else None)
        ep_loss = 0.0; ep_n = 0; te = time.time(); pend = None; pend_k = 0
        for bt in pf:
            codes, stm, wres, score, hce_l = to_dev(bt, dev, k)
            for g in opt.param_groups:
                g["lr"] = lr_at(step)
            blend = blend_at(step)
            if a.dev_scalars:  # v3b: one tiny H2D copy into preallocated device scalars (no new per-step scalar constants)
                sc_dev.copy_(torch.tensor([blend, 1.0 - blend], dtype=torch.float32))
                _, _, tg = targets_t(score, stm, wres, k, blend_t, omb_t)
            else:
                _, _, tg = targets(score, stm, wres, k, blend)
            opt.zero_grad(set_to_none=True)
            pred = torch.sigmoid(model(codes, stm, hce_l))
            loss = F.mse_loss(pred, tg)
            # QA util 2026-10-24: loss read back every --loss-sync-every steps (was every step; each read is a full CPU-GPU sync)
            ld = loss.detach() * len(codes); pend = ld if pend is None else pend + ld; pend_k += 1
            loss.backward(); opt.step(); model.project_weights()
            if clip_units:  # S-A2 --weight-clip (after v3c's int16-rail projection; never looser than it)
                model.clip_weights(clip_units)
            step += 1; n = len(codes); seen += n; ep_n += n
            if pend_k >= a.loss_sync_every or time.time() - last >= a.log_every:
                v = float(pend.cpu()); pend = None; pend_k = 0
                if not math.isfinite(v):
                    raise RuntimeError("non-finite loss")
                ls += v; ep_loss += v
            now = time.time()
            if now - last >= a.log_every:
                print(f"ep{ep + 1} step {step:,}/{total_steps:,} blend={blend:.3f} lr={lr_at(step):.2e} train_mse={ls / seen:.6f} {seen / (now - tstart):,.0f} pos/s", flush=True)
                mem_report(f"ep{ep + 1} step {step:,}", a.max_ram_gb)
                last = now
        if pend is not None:  # QA util: flush the last unsynced losses of the epoch
            v = float(pend.cpu()); pend = None; pend_k = 0
            if not math.isfinite(v):
                raise RuntimeError("non-finite loss")
            ls += v; ep_loss += v
        pf = None
        vs, nv = evaluate(model, hold, val_idx, dev, k, a.batch_size, blends=(1.0, 0.6, 0.8))
        print(f"EPOCH {ep + 1}/{a.epochs} done in {time.time() - te:.0f}s train_mse={ep_loss / max(ep_n, 1):.6f} | HOLDOUT n={nv:,} "
              f"mse_teacher={vs[1.0]:.6f} (HCE {base_sub[1.0]:.6f}, {100 * (1 - vs[1.0] / base_sub[1.0]):+.2f}%) "
              f"mse_b0.6={vs[0.6]:.6f} (HCE {base_sub[0.6]:.6f}, {100 * (1 - vs[0.6] / base_sub[0.6]):+.2f}%) mse_b0.8={vs[0.8]:.6f}", flush=True)
        stem = run / f"epoch{ep + 1:03d}-step{step:09d}"
        payload = {"config": config, "model": cpu_copy(model.state_dict()), "optimizer": cpu_copy(opt.state_dict()),
                   "next_epoch": ep + 1, "step": step, "val": {str(b): v for b, v in vs.items()}}
        atomic_write(stem.with_suffix(".pt"), lambda dst: torch.save(payload, dst))
        clip_report = export_forge(model, stem, k, bool(a.residual), clip_units)
        if clip_report:  # S-A2 --weight-clip: the verified export
            mx, at = clip_report["max_abs"], clip_report["at_bound"]
            print(f"INT16 CHECK {stem.name}: max|q| W1 {mx['W1']} B1 {mx['B1']} W2 {mx['W2']} B2 {mx['B2']} <= {clip_units}; at the clip "
                  f"bound W1 {at['W1']} B1 {at['B1']} W2 {at['W2']} B2 {at['B2']}; at the int16 rail {clip_report['at_int16_rail']}; "
                  f"lane bound {clip_report['lane_bound']:,} (< 2^24: {clip_report['lane_bound_below_2^24']}), int32 headroom "
                  f"x{clip_report['int32_headroom']:,}", flush=True)
        atomic_write(stem.with_suffix(".json"), lambda dst: dst.write((json.dumps({**config, "val": payload["val"], "baseline": {str(b): v for b, v in base_sub.items()}}, indent=1) + "\n").encode()))
        print(f"Saved {stem.name} (.pt .inc .bin .json)", flush=True)
        mem_report(f"epoch{ep + 1:03d}", a.max_ram_gb)
    finally:  # v3: join background epoch builder / prefetchers cleanly, also on exceptions
        if pf is not None:  # v3b: current producer first (with one order buffer the builder waits for it)
            pf.close()
        if nxt is not None:
            nxt.close()
    if a.final_full_val:
        full, nf = evaluate(model, hold, full_idx, dev, k, a.batch_size, blends=(1.0, 0.6, 0.8))
        bfull, _ = evaluate(model, hold, full_idx, dev, k, a.batch_size, blends=(1.0, 0.6, 0.8), baseline=True)
        print(f"FINAL FULL HOLDOUT n={nf:,}: net mse_teacher={full[1.0]:.6f} mse_b0.6={full[0.6]:.6f} mse_b0.8={full[0.8]:.6f} | HCE {bfull[1.0]:.6f}/{bfull[0.6]:.6f}/b0.8 {bfull[0.8]:.6f}", flush=True)
    print(f"Finished: {seen:,} positions in {time.time() - tstart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
