#!/usr/bin/env python3
# train_resid_v3.py: speed-only derivative of train_resid_v2.py (Forge trainer, AI-made for Couns). Changes: epoch-boundary prefetch overlap, packed H2D copy, loss-sync default 128. Same math.
# train_resid_v3b.py: RAM derivative of train_resid_v3a.py. --dev-scalars (per-step lr/blend/Adam factors as preallocated device tensors,
# filled by copy_, not new Python floats each step: suspected DirectML per-step host leak ~24 KB/step), int32 shuffle order in reused
# buffer(s), optional --mmap-data, private-memory logging + --max-ram-gb warning. Same order, same math (bit-identical on CPU).
"""Forge-768 residual NNUE trainer (GPU, DirectML/CPU). Own code, derived in structure from the
supplied train_nnue.py (md5 5A161C70...), but fed from pre-converted binaries:

  *.pos  (tools/fen2bin.cpp)  nibble boards + int16 teacher score (STM cp) + meta (stm, WHITE result)
  *.hce  (tools/hce_dump.cpp) int16 Forge-1ab50b2d evaluate_uncached (STM cp), line-aligned with .pos

Model/export are the same Forge net (768 -> H per perspective, SCReLU, 2H -> 1, int16 QAT, scale 4096).
--residual: logit = net(x) + K*hce/400, output layer starts at zero => first forward == HCE alone,
export writes FORGE_NNUE_RESIDUAL 1.  Loss = MSE(sigmoid(logit), blend*sigmoid(K*score/400) + (1-blend)*stm_result).
--pure (Opus O4): stand-alone net, logit = net(x) (no HCE term; same target), exports .fnn2 with the residual flag 0
for the engine's PureNnue option; .hce files are then optional (used only for the HCE-alone baseline report).
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
    hce = np.empty(total, np.int16) if need_hce else np.zeros(total, np.int16)  # O4 --pure without --hce-dir: zeros
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


class ZeroMap:
    """O4 --pure without --hce-dir: stands in for the HCE column (every value 0, nothing stored)."""
    def __getitem__(self, idx):
        return np.zeros(len(np.asarray(idx)), np.int16)


def load_set_mmap(pos_files, hce_dir, limit=None, need_hce=True):
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
        if need_hce:
            hp = Path(hce_dir) / (Path(p).stem + ".hce")
            with open(hp, "rb") as f:
                h = f.read(16)
            if h[:4] != b"FHCE" or int.from_bytes(h[8:16], "little") != n:
                raise ValueError(f"hce header/count mismatch {hp} vs {p}")
            hh = np.memmap(hp, np.int16, "r", 16, (n,))[:n_use]
            if (hh == -32768).any():
                raise ValueError(f"bad hce in {hp}")
            H.append(hh)
        B.append(b); S.append(s); M.append(m); offs.append(o); o += n_use
    return dict(boards=CatMap(B, offs, np.uint8, (32,)), score=CatMap(S, offs, np.int16), meta=CatMap(M, offs, np.uint8),
                hce=CatMap(H, offs, np.int16) if need_hce else ZeroMap(), n=total, files=[(p, n_use) for p, n, n_use in picks])


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


# ----------------------------------------------------------------------------- king buckets (Opus C4)
# Optional architecture, used only with --king-buckets N (N >= 1); without it everything above and below is
# the unchanged v3b trainer. Feature definition (identical in the engine, forge/nnue_v2.hpp):
#   perspective p (black = 1), own king on square k (first own king if a malformed record has several, square 0
#   if it has none), kr = k ^ 56 for black else k; flip = 7 if mirroring and kr % 8 >= 4 else 0;
#   index = king_map[kr] * 768 + (rel * 6 + type) * 64 + (rsq ^ flip)   (rel, type, rsq as in features()).
# Factoriser (--king-factor 1, default): every bucket's weights are bucket[b] + factor, where `factor` is one
# 768 x H block shared by all buckets during training; the export folds it in (inference cost unchanged).
# QAT and export use q(bucket[b] + factor), so the exported ints are exactly the trained forward's weights.
def king_features(codes, black, king_map, mirror, kb):
    """codes [B,64], black [B] -> feature indices [B,64] in [0, kb*768) (kb*768 = empty square) == the engine's."""
    sq = torch.arange(64, device=codes.device).unsqueeze(0)
    c = codes - 1
    color = torch.div(c, 6, rounding_mode="floor")
    typ = c - color * 6
    bl = black.unsqueeze(1)
    rel = (color != bl).long()
    rsq = torch.where(bl == 1, sq ^ 56, sq.expand_as(codes))
    own_king = torch.where(black == 1, 12, 6).unsqueeze(1)
    ksq = torch.argmax((codes == own_king).long(), dim=1)          # first own king, 0 if none
    kr = torch.where(black == 1, ksq ^ 56, ksq)
    flip = torch.where((kr & 7) >= 4, 7, 0) if mirror else torch.zeros_like(kr)
    bucket = king_map[kr]
    f = bucket.unsqueeze(1) * FEATURES + (rel * 6 + typ) * 64 + (rsq ^ flip.unsqueeze(1))
    return torch.where(codes > 0, f, torch.full_like(f, kb * FEATURES))


def king_dense(codes, black, king_map, mirror, kb):
    f = king_features(codes, black, king_map, mirror, kb)
    x = torch.zeros(codes.shape[0], kb * FEATURES + 1, device=codes.device).scatter_(1, f, 1.0)
    return x[:, :kb * FEATURES]


def king_map_from_args(buckets, map_text):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import forge_nnue_v2 as V2
    kmap = V2.parse_map(map_text) if map_text else V2.symmetric_map(V2.half_layout(buckets))
    if max(kmap) + 1 != buckets or min(kmap) < 0:
        raise ValueError(f"king map uses buckets 0..{max(kmap)}, expected 0..{buckets - 1}")
    return kmap


def quant_int(p):
    """The integers q() uses for p (float32, round half away from zero, clamp to int16), as int16 numpy."""
    s = p.detach().float().cpu() * SCALE
    r = torch.clamp(torch.sign(s) * torch.floor(torch.abs(s) + 0.5), -32767, 32767)
    return r.to(torch.int16).numpy()


class NNUEKB(nn.Module):
    def __init__(self, hidden, king_map, mirror=True, factor=True, qat=True, residual=True):
        super().__init__()
        self.hidden, self.qat, self.residual, self.mirror = hidden, qat, residual, bool(mirror)
        self.register_buffer("king_map", torch.tensor(king_map, dtype=torch.long))
        self.kb = max(king_map) + 1
        self.ft_w = nn.Parameter(torch.zeros(self.kb, hidden, FEATURES))
        self.ft_f = nn.Parameter(torch.zeros(hidden, FEATURES)) if factor else None
        self.ft_b = nn.Parameter(torch.zeros(hidden))
        self.out = nn.Linear(2 * hidden, 1)
        nn.init.normal_(self.ft_f if factor else self.ft_w, std=0.02)
        nn.init.zeros_(self.out.bias)
        if residual:
            nn.init.zeros_(self.out.weight)  # first forward == HCE alone

    q = NNUE.q
    project_weights = NNUE.project_weights

    def ft_sum(self):
        """Folded bucket weights [KB, H, 768] (before quantisation)."""
        return self.ft_w if self.ft_f is None else self.ft_w + self.ft_f.unsqueeze(0)

    def forward(self, codes, stm, hce_logit):
        w = self.q(self.ft_sum()).permute(1, 0, 2).reshape(self.hidden, self.kb * FEATURES)
        b = self.q(self.ft_b)
        hs = torch.clamp(F.linear(king_dense(codes, stm, self.king_map, self.mirror, self.kb), w, b), 0.0, 1.0).square()
        ho = torch.clamp(F.linear(king_dense(codes, 1 - stm, self.king_map, self.mirror, self.kb), w, b), 0.0, 1.0).square()
        out = F.linear(torch.cat([hs, ho], 1), self.q(self.out.weight), self.q(self.out.bias)).squeeze(1)
        return out + hce_logit if self.residual else out


def export_forge_v2(model, stem, residual):
    """Writes <stem>.fnn2 (format v2, see forge_nnue_v2.py) from the trained forward's quantised weights."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import forge_nnue_v2 as V2
    with torch.no_grad():
        if isinstance(model, NNUEKB):
            w1 = quant_int(model.ft_sum()).transpose(0, 2, 1)       # [KB, 768, H]
            b1 = quant_int(model.ft_b)
            kmap, kb, mirror = model.king_map.cpu().tolist(), model.kb, model.mirror
        else:
            w1 = quant_int(model.ft.weight).T[None]                 # [1, 768, H]
            b1 = quant_int(model.ft.bias)
            kmap, kb, mirror = [0] * 64, 1, False
        w2, b2 = quant_int(model.out.weight).ravel(), quant_int(model.out.bias).ravel()
    path = stem.with_suffix(".fnn2")
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        V2.write_v2(temp, hidden=model.hidden, king_buckets=kb, residual=residual, mirror=mirror, king_map=kmap,
                    w1=np.ascontiguousarray(w1).ravel(), b1=b1, w2=w2, b2=b2)
        if path.exists():
            raise FileExistsError(str(path))
        os.rename(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


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


def export_forge(model, stem, k, residual):
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
    ap.add_argument("--hce-dir", help="directory of the .hce files (required, except with --pure)")
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
    ap.add_argument("--king-buckets", type=int, default=0, help="C4: N >= 1 trains the king-bucketed input layer (standard layouts 1, 2, 4, 6, 8, 16, 32; see forge_nnue_v2.py) and exports .fnn2 (engine: NNUEFile + NNUEKingBuckets N); 0 = off (default, unchanged trainer)")
    ap.add_argument("--king-map", default="", help="C4: explicit king bucket map, 32 (half board, files a-d, ranks 1-8, mirrored symmetric) or 64 comma-separated entries")
    ap.add_argument("--king-mirror", type=int, choices=[0, 1], default=1, help="C4: mirror files e-h onto d-a per perspective (default 1)")
    ap.add_argument("--king-factor", type=int, choices=[0, 1], default=1, help="C4: shared factoriser block during training, folded into every bucket on export (default 1)")
    ap.add_argument("--export-v2", action="store_true", help="C4: also write <epoch>.fnn2 (format v2, 1 bucket) for the standard model")
    ap.add_argument("--pure", action="store_true", help="O4: stand-alone (pure) NNUE: the net predicts the whole score, logit = net(x) "
                    "with no HCE term (same target: blend of teacher score and game result); every epoch also writes .fnn2 with "
                    "the residual flag 0 (engine: NNUEFile + PureNnue 1); --hce-dir becomes optional (only the HCE-alone "
                    "baseline report needs it); not with --residual or --init-check")
    a = ap.parse_args()
    if a.pure and (a.residual or a.init_check):  # O4
        ap.error("--pure trains a stand-alone net: not with --residual or --init-check")
    if not a.hce_dir and (not a.pure or a.baseline_only):  # O4: --hce-dir was required=True before --pure existed
        ap.error("--hce-dir is required (it is optional only with --pure)")
    k = a.sigmoid_k
    if k != K_DEFAULT:
        print("WARNING: export needs sigmoid-k 2.25", flush=True)
    torch.manual_seed(a.seed)
    dev = device_for(a.device, a.device_index)
    run = Path(a.run_dir)
    run.mkdir(parents=True, exist_ok=bool(a.resume) or a.baseline_only)
    (run / f"settings_{int(time.time())}.txt").write_text(" ".join(sys.argv) + "\n" + json.dumps(vars(a), indent=1))
    t0 = time.time()
    hold_files = expand(a.holdout)
    hold = load_set(hold_files, a.hce_dir, need_hce=bool(a.hce_dir))
    print(f"holdout: {hold['n']:,} positions from {len(hold_files)} files ({time.time() - t0:.0f}s)", flush=True)
    rng = np.random.default_rng(12345)
    if a.val_positions and a.val_positions < hold["n"]:
        val_idx = np.sort(rng.choice(hold["n"], a.val_positions, replace=False))
    else:
        val_idx = np.arange(hold["n"], dtype=np.int64)
    full_idx = np.arange(hold["n"], dtype=np.int64)
    if a.king_buckets:
        kmap = king_map_from_args(a.king_buckets, a.king_map)
        model = NNUEKB(a.shape, kmap, mirror=bool(a.king_mirror), factor=bool(a.king_factor), qat=not a.no_qat,
                       residual=a.residual or a.baseline_only).to(dev)
        print(f"king buckets: {model.kb} mirror={model.mirror} factor={a.king_factor} map(rank 8 first, files a-h): "
              + " | ".join(" ".join(str(kmap[r * 8 + f]) for f in range(8)) for r in range(7, -1, -1)), flush=True)
    else:
        model = NNUE(a.shape, qat=not a.no_qat, residual=a.residual or a.baseline_only).to(dev)
    if a.hce_dir:
        base_sub, nb = evaluate(model, hold, val_idx, dev, k, a.batch_size, baseline=True)
        print(f"BASELINE HCE-alone holdout subset n={nb:,}: mse_teacher(blend1.0)={base_sub[1.0]:.6f} mse_blend0.6={base_sub[0.6]:.6f}", flush=True)
    else:  # O4 --pure without .hce files
        base_sub = None
        print("BASELINE HCE-alone: not computed (--pure without --hce-dir)", flush=True)
    if a.baseline_only:
        full, nf = evaluate(model, hold, full_idx, dev, k, a.batch_size, baseline=True)
        print(f"BASELINE HCE-alone holdout FULL n={nf:,}: mse_teacher={full[1.0]:.6f} mse_blend0.6={full[0.6]:.6f}", flush=True)
        # extra blends for reference
        ex, _ = evaluate(model, hold, full_idx, dev, k, a.batch_size, blends=(0.0, 0.4, 0.8), baseline=True)
        print("BASELINE extra blends full: " + " ".join(f"b{b}={v:.6f}" for b, v in ex.items()), flush=True)
        return 0
    if a.init_check:
        init, _ = evaluate(model, hold, val_idx, dev, k, a.batch_size)
        print(f"INIT residual net: mse_teacher={init[1.0]:.6f} mse_b0.6={init[0.6]:.6f} (baseline {base_sub[1.0]:.6f}/{base_sub[0.6]:.6f})", flush=True)
        if abs(init[1.0] - base_sub[1.0]) > 1e-6 or abs(init[0.6] - base_sub[0.6]) > 1e-6:
            print("INIT CHECK FAILED", flush=True)
            return 3
        print("INIT CHECK OK (residual init == HCE alone)", flush=True)
    train_files = expand(a.train)
    train_files = [f for f in train_files if f not in hold_files]
    t1 = time.time()
    train = (load_set_mmap if a.mmap_data else load_set)(train_files, a.hce_dir, limit=a.max_train or None,
                                                          need_hce=bool(a.hce_dir))
    N = train["n"]
    print(f"train: {N:,} positions from {len(train['files'])} files ({time.time() - t1:.0f}s load)", flush=True)
    spe = N // a.batch_size
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
    if a.king_buckets:  # C4 (absent for the standard model, so its checkpoints stay byte-identical)
        config.update({"features": "forge768-king-buckets", "king_buckets": model.kb, "king_mirror": model.mirror,
                       "king_factor": bool(a.king_factor), "king_map": model.king_map.cpu().tolist()})
    if a.pure:  # O4 (absent otherwise, so the other checkpoints stay byte-identical)
        config["pure"] = True

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
        np.random.default_rng(a.seed * 1000 + e).shuffle(buf)
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
        if base_sub is None:  # O4 --pure without .hce files: no HCE comparison
            print(f"EPOCH {ep + 1}/{a.epochs} done in {time.time() - te:.0f}s train_mse={ep_loss / max(ep_n, 1):.6f} | HOLDOUT n={nv:,} "
                  f"mse_teacher={vs[1.0]:.6f} mse_b0.6={vs[0.6]:.6f} mse_b0.8={vs[0.8]:.6f}", flush=True)
        else:
            print(f"EPOCH {ep + 1}/{a.epochs} done in {time.time() - te:.0f}s train_mse={ep_loss / max(ep_n, 1):.6f} | HOLDOUT n={nv:,} "
                  f"mse_teacher={vs[1.0]:.6f} (HCE {base_sub[1.0]:.6f}, {100 * (1 - vs[1.0] / base_sub[1.0]):+.2f}%) "
                  f"mse_b0.6={vs[0.6]:.6f} (HCE {base_sub[0.6]:.6f}, {100 * (1 - vs[0.6] / base_sub[0.6]):+.2f}%) mse_b0.8={vs[0.8]:.6f}", flush=True)
        stem = run / f"epoch{ep + 1:03d}-step{step:09d}"
        payload = {"config": config, "model": cpu_copy(model.state_dict()), "optimizer": cpu_copy(opt.state_dict()),
                   "next_epoch": ep + 1, "step": step, "val": {str(b): v for b, v in vs.items()}}
        atomic_write(stem.with_suffix(".pt"), lambda dst: torch.save(payload, dst))
        if a.king_buckets:  # C4: bucketed nets only exist as v2 files
            export_forge_v2(model, stem, bool(a.residual))
        else:
            export_forge(model, stem, k, bool(a.residual))
            if a.export_v2 or a.pure:  # O4: a pure net is used through NNUEFile + PureNnue, i.e. as a v2 file
                export_forge_v2(model, stem, bool(a.residual))
        atomic_write(stem.with_suffix(".json"), lambda dst: dst.write((json.dumps({**config, "val": payload["val"], "baseline": {str(b): v for b, v in (base_sub or {}).items()}}, indent=1) + "\n").encode()))
        print(f"Saved {stem.name} (.pt .fnn2 .json)" if a.king_buckets else
              f"Saved {stem.name} (.pt .inc .bin .json{' .fnn2' if a.export_v2 or a.pure else ''})", flush=True)
        mem_report(f"epoch{ep + 1:03d}", a.max_ram_gb)
    finally:  # v3: join background epoch builder / prefetchers cleanly, also on exceptions
        if pf is not None:  # v3b: current producer first (with one order buffer the builder waits for it)
            pf.close()
        if nxt is not None:
            nxt.close()
    if a.final_full_val:
        full, nf = evaluate(model, hold, full_idx, dev, k, a.batch_size, blends=(1.0, 0.6, 0.8))
        if base_sub is None:  # O4 --pure without .hce files
            print(f"FINAL FULL HOLDOUT n={nf:,}: net mse_teacher={full[1.0]:.6f} mse_b0.6={full[0.6]:.6f} mse_b0.8={full[0.8]:.6f}", flush=True)
        else:
            bfull, _ = evaluate(model, hold, full_idx, dev, k, a.batch_size, blends=(1.0, 0.6, 0.8), baseline=True)
            print(f"FINAL FULL HOLDOUT n={nf:,}: net mse_teacher={full[1.0]:.6f} mse_b0.6={full[0.6]:.6f} mse_b0.8={full[0.8]:.6f} | HCE {bfull[1.0]:.6f}/{bfull[0.6]:.6f}/b0.8 {bfull[0.8]:.6f}", flush=True)
    print(f"Finished: {seen:,} positions in {time.time() - tstart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
