#!/usr/bin/env python
"""train_h512_gpu.py - JOB E (2026-11-11): GPU trainer for Forge's standalone H512 NNUE v3 net (FORGENN3).

Own code. It reuses FB2's model, clipping and exporter (fable_nnue_train.py / fable_nnue_v3.py in this folder) and
can call the R7 Triton feature-transformer kernel. That kernel file is GPL-3.0 tool code of the nnue-pytorch AMD port;
it is imported at run time from its own folder (H512_KERNELS_DIR) and none of its text is copied here.

What is different from FB2's CPU trainer:
  * Data: every FPOS training row is held on the GPU (boards 32 B, score int16, meta u8). One epoch is one random
    permutation of all rows (numpy PCG64 seeded with [seed, epoch]), so every row has exactly the same sampling
    probability and the data position is (epoch, offset): exact on resume.
  * Features are computed on the GPU from the 4-bit piece codes (same formula as FB2's perspective_indices), 32 slots
    per perspective, -1 = empty.
  * Forward: fake-quantised weights (FB2's QAT) through the Triton kernel, or plain torch embedding_bag (--backend).
  * Schedule: a plan file with stages; each stage is one warm-up + cosine cycle that ends at a cumulative number of
    presentations. Target per step: (1 - alpha) * sigmoid(score * 2.25 / 400) + alpha * result_from_side_to_move.
  * Checkpoints hold model, Adam, schedule position, RNG states and the data position; exports are scored with an
    exact integer forward on the GPU (the engine's arithmetic: truncating divisions, clamps).

Commands:
  train      --plan plan.json --run-dir DIR [--resume] [--backend triton|plain] [--max-pres N]
  score      --net NET.fnn3 --pos P.pos [--name N] [--out J.json] [--final-test-unlock]
  selfcheck  --pos P.pos [--ckpt FB2_ckpt.pt] [--net NET.fnn3] [--rows N]
"""
import argparse
import glob
import hashlib
import importlib
import importlib.util
import json
import math
import os
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fable_nnue_v3 as v3      # noqa: E402
import fable_nnue_train as fb   # noqa: E402

import torch                    # noqa: E402
import torch.nn.functional as F  # noqa: E402

K_SIG = fb.K
QA, QB = fb.QA, fb.QB
SLOTS = 32
KERNELS_DIR = os.environ.get(
    "H512_KERNELS_DIR", r"D:\grok-pc-data\dwqww\.claude\worktrees\opus-r7-speed\tools\nnue_pytorch_amd\forge_v2")
KERNELS_MD5 = "916539cef784f791d7d3ed91e61e05f1"   # the pin used by train_forge_v2_fast_ckpt.py
KER = None
BLENDS = (1.0, 0.8, 0.75, 0.6, 0.5, 0.0)           # blend b = 1 - alpha; b0.6 is the ranking metric


# ---------------------------------------------------------------- kernels

def load_kernels():
    """Import the R7 Triton kernels from their own folder. Returns (ok, text)."""
    global KER
    path = os.path.join(KERNELS_DIR, "forge_v2_kernels.py")
    if not os.path.isfile(path):
        return False, f"kernels file missing: {path}"
    h = hashlib.md5(open(path, "rb").read()).hexdigest()
    if h != os.environ.get("H512_KERNELS_MD5", KERNELS_MD5):
        return False, f"kernels md5 {h} != pinned {KERNELS_MD5}"
    try:
        # 2026-11-11: venv\Lib\site-packages\_rocm_sdk_devel\include denies access to this account, so Triton's driver
        # cannot compile its small HIP helper against it. The same headers are readable in _rocm_sdk_core\include;
        # add that folder to the driver's include list for this process (no installation or ACL is changed).
        import triton.backends.amd.driver as drv
        import _rocm_sdk_core
        inc = os.path.join(os.path.dirname(os.path.abspath(_rocm_sdk_core.__file__)), "include")
        if os.path.isfile(os.path.join(inc, "hip", "hip_runtime.h")) and inc not in drv.include_dirs:
            drv.include_dirs.insert(1, inc)
        if KERNELS_DIR not in sys.path:
            sys.path.insert(0, KERNELS_DIR)
        KER = importlib.import_module("forge_v2_kernels")
    except Exception as e:
        return False, f"import: {type(e).__name__}: {e}"
    return True, h


# ---------------------------------------------------------------- data

def fpos_header(path):
    with open(path, "rb") as f:
        head = f.read(16)
    if head[:4] != b"FPOS":
        raise SystemExit(f"{path}: not an FPOS file")
    return int(np.frombuffer(head[8:16], "<u8")[0])


def load_fpos_gpu(files, dev, log=print):
    """All rows of the FPOS files as device tensors: boards [N,32] u8, score [N] i16, meta [N] u8, row counts."""
    counts = [fpos_header(f) for f in files]
    n = int(sum(counts))
    boards = torch.empty((n, 32), dtype=torch.uint8, device=dev)
    score = torch.empty((n,), dtype=torch.int16, device=dev)
    meta = torch.empty((n,), dtype=torch.uint8, device=dev)
    o = 0
    t0 = time.time()
    for f, c in zip(files, counts):
        b = np.fromfile(f, np.uint8, c * 32, offset=16).reshape(c, 32)
        s = np.fromfile(f, "<i2", c, offset=16 + 32 * c)
        m = np.fromfile(f, np.uint8, c, offset=16 + 34 * c)
        boards[o:o + c].copy_(torch.from_numpy(b))
        score[o:o + c].copy_(torch.from_numpy(s))
        meta[o:o + c].copy_(torch.from_numpy(m))
        o += c
    log(f"data: {len(files)} files, {n} rows on {dev} in {time.time() - t0:.1f}s")
    return boards, score, meta, counts


def load_hce_gpu(files, dev):
    out = []
    for f in files:
        with open(f, "rb") as fh:
            head = fh.read(16)
        if head[:4] != b"FHCE":
            raise SystemExit(f"{f}: not an FHCE file")
        c = int(np.frombuffer(head[8:16], "<u8")[0])
        out.append(torch.from_numpy(np.fromfile(f, "<i2", c, offset=16)).to(dev))
    return torch.cat(out)


class Tables:
    def __init__(self, cfg, dev):
        self.kb = cfg["king_buckets"]
        self.nf = self.kb * 768
        self.mirror = bool(cfg["mirror"])
        self.king_map = torch.tensor(cfg["king_map"], dtype=torch.int32, device=dev)
        self.output_map = torch.tensor(cfg["output_map"], dtype=torch.int64, device=dev)
        self.phase_map = torch.tensor(v3.output_layout(fb.PHASES), dtype=torch.int64, device=dev)
        self.sq = torch.arange(64, dtype=torch.int32, device=dev)
        self.sq56 = self.sq ^ 56
        self.lut = torch.arange(self.nf, dtype=torch.int32, device=dev)     # identity: indices are Forge indices


def features(boards_b, meta_b, T):
    """GPU version of FB2's perspective_indices/batch_features.
    Returns us_white [B] f32 (1 = White to move), wi, bi [B,32] i32 (white / black perspective, -1 empty),
    ob [B] i64 (output bucket), phase [B] i64."""
    B = boards_b.shape[0]
    codes = torch.empty((B, 64), dtype=torch.int32, device=boards_b.device)
    codes[:, 0::2] = (boards_b & 15).to(torch.int32)
    codes[:, 1::2] = (boards_b >> 4).to(torch.int32)
    occ = codes != 0
    ptype = torch.remainder(codes - 1, 6)

    def persp(white):
        if white:
            rel = (codes >= 7).to(torch.int32)
            kr = torch.argmax((codes == 6).to(torch.uint8), dim=1).to(torch.int32)
            sq = T.sq
        else:
            rel = ((codes >= 1) & (codes <= 6)).to(torch.int32)
            kr = torch.argmax((codes == 12).to(torch.uint8), dim=1).to(torch.int32) ^ 56
            sq = T.sq56
        bucket = T.king_map[kr.long()]
        if T.mirror:
            flip = torch.where((kr & 7) >= 4, 7, 0).to(torch.int32)
        else:
            flip = torch.zeros_like(kr)
        idx = bucket[:, None] * 768 + (rel * 6 + ptype) * 64 + (sq[None, :] ^ flip[:, None])
        idx = torch.where(occ, idx, torch.full_like(idx, -1))
        return torch.topk(idx, SLOTS, dim=1, sorted=False).values

    wi, bi = persp(True), persp(False)
    pieces = occ.sum(dim=1).clamp(max=32)
    us_white = 1.0 - (meta_b & 1).to(torch.float32)
    return us_white, wi, bi, T.output_map[pieces], T.phase_map[pieces]


def targets(score_b, meta_b, dtype=torch.float32):
    teacher = torch.sigmoid(torch.clamp(score_b.to(dtype) * (K_SIG / 400.0), -40.0, 40.0))
    stm = (meta_b & 1)
    white = (meta_b >> 1).to(dtype) * 0.5
    res = torch.where(stm == 0, white, 1.0 - white)
    return teacher, res


# ---------------------------------------------------------------- forward passes

def forward_triton(model, cfg, us_white, wi, bi, ob, T, quant=True):
    w1, b1, w2, b2 = model.quantised() if quant else (model.merged_w1(), model.b1, model.w2, model.b2)
    x = KER.ForgeV2FT.apply(us_white, wi, bi, T.lut, w1, b1)
    out = (x @ w2.t()).gather(1, ob.view(-1, 1)).view(-1) + b2[ob]
    return out * cfg["eval_scale"]


def forward_plain(model, cfg, us_white, wi, bi, ob, T, quant=True):
    w1, b1, w2, b2 = model.quantised() if quant else (model.merged_w1(), model.b1, model.w2, model.b2)
    table = torch.cat([w1, torch.zeros(1, w1.shape[1], dtype=w1.dtype, device=w1.device)], dim=0)
    pad = T.nf
    wl = torch.where(wi < 0, pad, wi).long()
    bl = torch.where(bi < 0, pad, bi).long()
    aw = F.embedding_bag(wl, table, mode="sum", padding_idx=pad) + b1
    ab = F.embedding_bag(bl, table, mode="sum", padding_idx=pad) + b1
    u = us_white.view(-1, 1)
    ours = u * aw + (1 - u) * ab
    theirs = u * ab + (1 - u) * aw
    x = torch.cat([ours.clamp(0, 1) ** 2, theirs.clamp(0, 1) ** 2], dim=1)
    out = (x @ w2.t()).gather(1, ob.view(-1, 1)).view(-1) + b2[ob]
    return out * cfg["eval_scale"]


class IntNet:
    """A FORGENN3 file as device integer tensors, for the exact integer forward."""

    def __init__(self, path, dev):
        net = v3.read_net(path)
        self.hidden, self.eval_scale = net.hidden, net.eval_scale
        self.cfg = {"king_buckets": net.king_buckets, "mirror": net.mirror, "king_map": list(net.king_map),
                    "output_map": list(net.output_map), "eval_scale": net.eval_scale}
        self.residual = net.residual
        H = net.hidden
        w1 = np.concatenate([np.asarray(net.w1).reshape(-1, H), np.zeros((1, H), np.int64)], axis=0)
        self.w1 = torch.from_numpy(w1.astype(np.int32)).to(dev)
        self.b1 = torch.from_numpy(np.asarray(net.b1).astype(np.int32)).to(dev)
        self.w2 = torch.from_numpy(np.asarray(net.w2).astype(np.int64)).to(dev)
        self.b2 = torch.from_numpy(np.asarray(net.b2).astype(np.int64)).to(dev)
        self.pad = w1.shape[0] - 1


def forward_int(inet, us_white, wi, bi, ob):
    """Exact engine arithmetic: cp (int64), side to move's point of view."""
    H = inet.hidden
    wl = torch.where(wi < 0, inet.pad, wi).long()
    bl = torch.where(bi < 0, inet.pad, bi).long()
    aw = inet.w1[wl].sum(dim=1) + inet.b1
    ab = inet.w1[bl].sum(dim=1) + inet.b1
    u = (us_white > 0.5).view(-1, 1)
    ours = torch.where(u, aw, ab).clamp(0, QA).long()
    theirs = torch.where(u, ab, aw).clamp(0, QA).long()
    w2 = inet.w2[ob]
    total = (ours * ours * w2[:, :H]).sum(dim=1) + (theirs * theirs * w2[:, H:]).sum(dim=1)
    out = torch.div(total, QA, rounding_mode="trunc") + inet.b2[ob]
    cp = torch.div(out * inet.eval_scale, QA * QB, rounding_mode="trunc")
    return cp.clamp(-30000, 30000)


@torch.no_grad()
def score_int(net_path, boards, score, meta, dev, hce=None, chunk=8192, return_cp=False):
    """Exact integer MSE of a net file on FPOS rows held on the device (float64 loss)."""
    inet = IntNet(net_path, dev)
    T = Tables(inet.cfg, dev)
    n = boards.shape[0]
    sums = {b: torch.zeros((), dtype=torch.float64, device=dev) for b in BLENDS}
    ph_sum = torch.zeros(fb.PHASES, dtype=torch.float64, device=dev)
    ph_n = torch.zeros(fb.PHASES, dtype=torch.int64, device=dev)
    cps = []
    for s in range(0, n, chunk):
        bb, mm, ss = boards[s:s + chunk], meta[s:s + chunk], score[s:s + chunk]
        us_white, wi, bi, ob, phase = features(bb, mm, T)
        cp = forward_int(inet, us_white, wi, bi, ob)
        if return_cp:
            cps.append(cp)
        logit = cp.to(torch.float64) * (K_SIG / 400.0)
        if inet.residual:
            logit = logit + hce[s:s + chunk].to(torch.float64) * (K_SIG / 400.0)
        pred = torch.sigmoid(logit)
        teacher, res = targets(ss, mm, torch.float64)
        for b in BLENDS:
            err = (pred - (b * teacher + (1.0 - b) * res)) ** 2
            sums[b] += err.sum()
            if b == 0.6:
                ph_sum.index_add_(0, phase, err)
                ph_n.index_add_(0, phase, torch.ones_like(phase))
    out = {f"mse_b{b}": float(sums[b] / n) for b in BLENDS}
    out["rows"] = int(n)
    out["phase_rows"] = ph_n.tolist()
    out["phase_mse_b0.6"] = [float(ph_sum[i] / ph_n[i]) if int(ph_n[i]) else None for i in range(fb.PHASES)]
    if return_cp:
        return out, torch.cat(cps)
    return out


def export_cpu(model, cfg, path):
    cpu = fb.build_model(cfg, torch)
    cpu.load_state_dict({k: v.detach().cpu() for k, v in model.state_dict().items()})
    return fb.export_net(cpu, cfg, path, torch)


# ---------------------------------------------------------------- thermal / disk holds

class Guard:
    """Own holds, mirroring the owner's gpu_guard.ps1 limits (fan-curve column): pause at hot spot >= 76 C or memory
    junction >= 86 C, resume at <= 72 / <= 83; throttle between; no fresh sensor feed -> pause, after 300 s run at
    half duty. Disk: pause while any of C:, D:, F: has less than the floor free."""
    FEEDS = [r"C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv", r"F:\forge_nnue_train\adlx_sensors.csv"]
    HARD = (76.0, 86.0)
    RESUME = (72.0, 83.0)
    STALE = 30.0

    def __init__(self, log, floor_gb=20.5, enabled=True):
        self.log, self.floor, self.enabled = log, floor_gb, enabled
        self.last = 0.0
        self.r = 0.0
        self.blind_since = None
        self.holds = 0
        self.hold_seconds = 0.0
        self.max_hot = 0.0
        self.max_mj = 0.0
        self.cols = {}

    def read(self):
        for f in self.FEEDS:
            try:
                if time.time() - os.path.getmtime(f) > self.STALE:
                    continue
                if f not in self.cols:
                    with open(f, "r", encoding="latin-1") as fh:
                        hdr = fh.readline().strip().split(",")
                    ih = [i for i, h in enumerate(hdr) if "GPU Hot Spot Temperature" in h]
                    im = [i for i, h in enumerate(hdr) if "GPU Memory Junction Temperature" in h]
                    if not ih or not im:
                        continue
                    self.cols[f] = (ih[0], im[0], len(hdr))
                ih, im, nh = self.cols[f]
                with open(f, "rb") as fh:
                    fh.seek(0, 2)
                    size = fh.tell()
                    fh.seek(max(0, size - 4096))
                    lines = fh.read().decode("latin-1").strip().splitlines()
                for line in reversed(lines[-3:]):
                    x = line.split(",")
                    if len(x) >= nh - 1:
                        try:
                            return float(x[ih].replace('"', "")), float(x[im].replace('"', "")), os.path.basename(f)
                        except ValueError:
                            continue
            except OSError:
                continue
        return None

    def disk_low(self):
        low = []
        for d in ("C:\\", "D:\\", "F:\\"):
            try:
                free = shutil.disk_usage(d).free / 2 ** 30
                if free < self.floor:
                    low.append(f"{d} {free:.1f} GB")
            except OSError:
                pass
        return low

    def check(self, force=False):
        """Called from the training loop. Blocks while a hold is active. Returns the throttle ratio r (0..0.7)."""
        if not self.enabled:
            return 0.0
        now = time.time()
        if not force and now - self.last < 10.0:
            return self.r
        self.last = now
        t_hold = None
        while True:
            v = self.read()
            low = self.disk_low()
            hot_hold = False
            if v is None:
                if self.blind_since is None:
                    self.blind_since = time.time()
                blind = time.time() - self.blind_since
                if blind < 300:
                    hot_hold = True
                    why = f"no fresh sensor feed for {blind:.0f}s"
                else:
                    self.r = max(self.r, 0.5)
                    why = ""
            else:
                self.blind_since = None
                hot, mj, src = v
                self.max_hot, self.max_mj = max(self.max_hot, hot), max(self.max_mj, mj)
                if t_hold is None:
                    if hot >= self.HARD[0] or mj >= self.HARD[1]:
                        hot_hold = True
                else:
                    if hot > self.RESUME[0] or mj > self.RESUME[1]:
                        hot_hold = True
                why = f"hot={hot} memj={mj} ({src})"
                if not hot_hold:
                    if hot >= self.RESUME[0] or mj >= self.RESUME[1]:
                        self.r = min(0.7, self.r + 0.1)
                    elif hot <= self.RESUME[0] - 2 and mj <= self.RESUME[1] - 2:
                        self.r = max(0.0, self.r - 0.1)
            if low:
                why = (why + "; " if why else "") + "disk below floor: " + ", ".join(low)
            if not hot_hold and not low:
                break
            if t_hold is None:
                t_hold = time.time()
                self.holds += 1
                self.log(f"HOLD start: {why}")
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            time.sleep(5.0)
        if t_hold is not None:
            dt = time.time() - t_hold
            self.hold_seconds += dt
            self.log(f"HOLD end after {dt:.0f}s (throttle r={self.r:.1f})")
        return self.r


# ---------------------------------------------------------------- training

def stage_lr(step, steps, st, plan):
    wu = int(st.get("warmup_steps", plan.get("warmup_steps", 500)))
    peak = float(st["lr_peak"])
    final = peak * float(st.get("lr_final_frac", plan.get("lr_final_frac", 0.05)))
    if wu and step < wu:
        return peak * (step + 1) / wu
    frac = min(step / max(steps, 1), 1.0)
    return final + 0.5 * (peak - final) * (1.0 + math.cos(math.pi * frac))


def stage_alpha(step, steps, st):
    a0, a1 = float(st["alpha_start"]), float(st["alpha_end"])
    return a0 + (a1 - a0) * min(step / max(steps, 1), 1.0)


def make_perm(seed, epoch, n, dev):
    rng = np.random.Generator(np.random.PCG64([int(seed), int(epoch)]))
    return torch.from_numpy(rng.permutation(n).astype(np.int32)).to(dev)


def atomic_save(obj, path):
    tmp = path + ".partial"
    with open(tmp, "wb") as f:
        torch.save(obj, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def cmd_train(a):
    plan = json.load(open(a.plan, "r", encoding="utf-8"))
    os.makedirs(a.run_dir, exist_ok=True)
    logf = open(os.path.join(a.run_dir, "log.txt"), "a", encoding="utf-8", newline="\n")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    dev = torch.device("cuda")
    torch.manual_seed(int(plan["seed"]))
    say(f"train_h512_gpu start pid {os.getpid()} plan {a.plan} md5 {hashlib.md5(open(a.plan, 'rb').read()).hexdigest()} "
        f"torch {torch.__version__} hip {torch.version.hip} gpu {torch.cuda.get_device_name(0)}")
    backend = a.backend
    if backend == "triton":
        ok, why = load_kernels()
        if ok:
            try:
                ok, why2 = KER.triton_usable(dev)
                why = f"{why}; probe {why2}"
            except Exception as e:
                ok, why = False, f"{type(e).__name__}: {e}"
        say(f"triton: {'OK' if ok else 'UNUSABLE'} ({why})")
        if not ok:
            if a.no_fallback:
                raise SystemExit("triton unusable and --no-fallback given")
            backend = "plain"
    fwd = forward_triton if backend == "triton" else forward_plain
    say(f"backend {backend}")

    latest = os.path.join(a.run_dir, "latest.pt")
    resume = a.resume and os.path.isfile(latest)
    if resume:
        ck = torch.load(latest, map_location="cpu", weights_only=False)
        cfg = ck["cfg"]
    else:
        fb2 = torch.load(plan["init_fb2"], map_location="cpu", weights_only=False)
        cfg = dict(fb2["cfg"])
        if "king_map" not in cfg:
            cfg["king_map"] = v3.king_layout(cfg["king_buckets"])
            cfg["output_map"] = v3.output_layout(cfg["output_buckets"])
    model = fb.build_model(cfg, torch)
    model.load_state_dict(ck["state"] if resume else fb2["state"])
    model = model.to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    B = int(plan["batch"])
    stages = plan["stages"]
    prior = int(plan["prior_seen"])
    st_state = {"seen": prior, "stage": 0, "stage_step": 0, "epoch": 0, "offset": 0, "global_step": 0,
                "train_seconds": 0.0, "checkpoints": [], "best": None, "stage_ends": [], "stop_reason": "",
                "next_ckpt_seen": None}
    if resume:
        opt.load_state_dict(ck["opt"])
        st_state = ck["train_state"]
        torch.set_rng_state(ck["torch_rng"])
        if ck.get("cuda_rng") is not None:
            torch.cuda.set_rng_state_all(ck["cuda_rng"])
        say(f"resumed {latest}: seen {st_state['seen']} stage {st_state['stage']} stage_step {st_state['stage_step']} "
            f"epoch {st_state['epoch']} offset {st_state['offset']}")
    elif not plan.get("fresh_optimizer", True):
        opt.load_state_dict(fb2["opt"])
        say("optimizer state taken from the init checkpoint")
    else:
        say(f"init from {plan['init_fb2']} (prior presentations {prior}), fresh Adam")
    T = Tables(cfg, dev)

    files = sorted(glob.glob(plan["train_glob"]))
    if not files:
        raise SystemExit("no training files")
    boards, score, meta, counts = load_fpos_gpu(files, dev, say)
    N = boards.shape[0]
    sel = {}
    for item in plan["score_sets"]:
        sb, ss, sm, _ = load_fpos_gpu([item["pos"]], dev, lambda m: None)
        sel[item["name"]] = (sb, ss, sm)
        say(f"score set {item['name']}: {sb.shape[0]} rows {item['pos']}")
    metric_set, metric_key = plan["metric_set"], plan.get("metric_key", "mse_b0.6")
    phase_w = None
    if plan.get("phase_weight", "natural") == "equal":
        cnt = torch.zeros(fb.PHASES, dtype=torch.float64, device=dev)
        for s in range(0, N, 1 << 22):
            pieces = (boards[s:s + (1 << 22)] & 15).ne(0).sum(1) + (boards[s:s + (1 << 22)] >> 4).ne(0).sum(1)
            cnt += torch.bincount(T.phase_map[pieces.clamp(max=32)], minlength=fb.PHASES).to(torch.float64)
        phase_w = (cnt.sum() / (fb.PHASES * cnt)).to(torch.float32)
        say(f"phase weights (equal weight per bin): {[round(float(x), 4) for x in phase_w]}")
    guard = Guard(say, enabled=not a.no_guard)
    guard.check(force=True)

    def bounds(i):
        start = prior if i == 0 else int(stages[i - 1]["end_seen"])
        end = int(stages[i]["end_seen"])
        return start, end, int(math.ceil((end - start) / B))

    def save(tag=None):
        torch.cuda.synchronize()
        obj = {"cfg": cfg, "state": model.state_dict(), "opt": opt.state_dict(), "train_state": st_state,
               "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all(), "plan": plan,
               "data_position": {"epoch": st_state["epoch"], "offset": st_state["offset"], "seed": plan["seed"],
                                 "rows": N, "perm": "numpy PCG64([seed, epoch]).permutation(rows)"}}
        atomic_save(obj, latest)
        if tag:
            shutil.copyfile(latest, os.path.join(a.run_dir, f"{tag}.pt"))

    def checkpoint(reason, stage_end=False):
        t0 = time.time()
        seen = st_state["seen"]
        net_path = os.path.join(a.run_dir, f"net_seen{seen:011d}.fnn3")
        checksum, mw1, mb1, mw2 = export_cpu(model, cfg, net_path)
        entry = {"index": len(st_state["checkpoints"]) + 1, "seen": seen, "stage": stages[st_state["stage"]]["name"],
                 "stage_step": st_state["stage_step"], "global_step": st_state["global_step"], "reason": reason,
                 "stage_end": stage_end, "net": os.path.basename(net_path), "checksum": f"{checksum:x}",
                 "train_seconds": round(st_state["train_seconds"], 1), "lr": cur["lr"], "alpha": cur["alpha"],
                 "train_loss_ema": cur["ema"], "pos_per_s": cur["rate"], "epoch": st_state["epoch"],
                 "max_w1": mw1, "max_b1": mb1, "max_w2": mw2, "wall": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "holds": guard.holds, "hold_seconds": round(guard.hold_seconds, 1), "scores": {}}
        for name, (sb, ss, sm) in sel.items():
            entry["scores"][name] = score_int(net_path, sb, ss, sm, dev)
        m = entry["scores"][metric_set][metric_key]
        entry["metric"] = m
        st_state["checkpoints"].append(entry)
        new_best = st_state["best"] is None or m < st_state["best"]["metric"]
        if new_best:
            st_state["best"] = {"metric": m, "seen": seen, "net": entry["net"]}
            shutil.copyfile(net_path, os.path.join(a.run_dir, "best.fnn3"))
        save("best" if new_best else None)
        if stage_end:
            shutil.copyfile(latest, os.path.join(a.run_dir, f"stage_{stages[st_state['stage']]['name']}.pt"))
        with open(os.path.join(a.run_dir, "metrics.jsonl"), "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        with open(os.path.join(a.run_dir, "status.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"train_state": st_state, "backend": backend, "pid": os.getpid(), "plan": a.plan,
                       "max_hot": guard.max_hot, "max_memj": guard.max_mj}, f, indent=1, sort_keys=True)
        say(f"CKPT {entry['index']} seen {seen} stage {entry['stage']} {reason} {metric_set}.{metric_key} {m:.6f} "
            f"{'BEST ' if new_best else ''}b1.0 {entry['scores'][metric_set]['mse_b1.0']:.6f} lr {cur['lr']:.2e} "
            f"alpha {cur['alpha']:.3f} ema {cur['ema']:.6f} {cur['rate']:.0f} pos/s ({time.time() - t0:.1f}s)")
        return m

    every = int(plan.get("ckpt_every_pres", 250_000_000))
    if st_state["next_ckpt_seen"] is None:
        st_state["next_ckpt_seen"] = (st_state["seen"] // every + 1) * every
    perm = make_perm(plan["seed"], st_state["epoch"], N, dev)
    cur = {"lr": 0.0, "alpha": 0.0, "ema": None, "rate": 0.0}
    max_pres = a.max_pres
    pres_this_run = 0
    t_run = time.time()
    t_mark, seen_mark = time.time(), st_state["seen"]
    idx_hash = hashlib.sha256() if a.hash_indices else None
    stop_flag = os.path.join(a.run_dir, "STOP")
    r = 0.0
    model.train()
    while st_state["stage"] < len(stages) and not st_state["stop_reason"]:
        i = st_state["stage"]
        st = stages[i]
        start_seen, end_seen, steps = bounds(i)
        step = st_state["stage_step"]
        if step == 0:
            say(f"STAGE {st['name']} start: seen {st_state['seen']} -> {end_seen} ({steps} steps of {B}) lr_peak {st['lr_peak']} "
                f"alpha {st['alpha_start']}->{st['alpha_end']}")
        while step < steps:
            lr = stage_lr(step, steps, st, plan)
            alpha = stage_alpha(step, steps, st)
            for g in opt.param_groups:
                g["lr"] = lr
            off = st_state["offset"]
            if off + B <= N:
                idx = perm[off:off + B]
                st_state["offset"] = off + B
            else:
                head = perm[off:]
                st_state["epoch"] += 1
                perm = make_perm(plan["seed"], st_state["epoch"], N, dev)
                need = B - head.shape[0]
                idx = torch.cat([head, perm[:need]])
                st_state["offset"] = need
            if idx_hash is not None:
                idx_hash.update(idx.cpu().numpy().tobytes())
            bb = boards.index_select(0, idx)
            mm = meta.index_select(0, idx)
            ss = score.index_select(0, idx)
            us_white, wi, bi, ob, phase = features(bb, mm, T)
            cp = fwd(model, cfg, us_white, wi, bi, ob, T)
            teacher, res = targets(ss, mm)
            err = (torch.sigmoid(cp * (K_SIG / 400.0)) - ((1.0 - alpha) * teacher + alpha * res)) ** 2
            loss = (err * phase_w[phase]).mean() if phase_w is not None else err.mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            model.clip()
            step += 1
            st_state["stage_step"] = step
            st_state["global_step"] += 1
            st_state["seen"] += B
            pres_this_run += B
            if step % 100 == 0 or step == steps:
                lv = float(loss.detach())
                cur["ema"] = lv if cur["ema"] is None else 0.9 * cur["ema"] + 0.1 * lv
                now = time.time()
                cur["rate"] = (st_state["seen"] - seen_mark) / max(now - t_mark, 1e-9)
                st_state["train_seconds"] += now - t_mark
                t_mark, seen_mark = now, st_state["seen"]
                cur["lr"], cur["alpha"] = lr, alpha
                if step % a.log_every == 0 or step == steps:
                    say(f"step {st_state['global_step']} {st['name']}:{step}/{steps} seen {st_state['seen']} loss {lv:.6f} "
                        f"ema {cur['ema']:.6f} lr {lr:.2e} alpha {alpha:.3f} {cur['rate']:.0f} pos/s r={r:.1f} "
                        f"hot/memj max {guard.max_hot:.0f}/{guard.max_mj:.0f} epoch {st_state['epoch']} "
                        f"offset {st_state['offset']} idxsum {int(idx.long().sum())}")
                r = guard.check()
                t_mark = time.time()
                if r > 0:
                    time.sleep(min(30.0, (100 * B / max(cur["rate"], 1.0)) * r / (1.0 - r)))
                    t_mark = time.time()
                if os.path.exists(stop_flag):
                    st_state["stop_reason"] = "STOP flag"
                    break
                if max_pres and pres_this_run >= max_pres:
                    st_state["stop_reason"] = f"--max-pres {max_pres}"
                    break
                if a.max_minutes and (time.time() - t_run) / 60.0 >= a.max_minutes:
                    st_state["stop_reason"] = f"--max-minutes {a.max_minutes}"
                    break
            if step < steps and st_state["seen"] >= st_state["next_ckpt_seen"]:
                st_state["next_ckpt_seen"] = (st_state["seen"] // every + 1) * every
                checkpoint("interval")
                t_mark, seen_mark = time.time(), st_state["seen"]
        if st_state["stop_reason"]:
            break
        cur["lr"], cur["alpha"] = stage_lr(steps - 1, steps, st, plan), stage_alpha(steps, steps, st)
        prev = [e["metric"] for e in st_state["stage_ends"]]
        ref = plan.get("reference_metric")
        prev_best = min(prev + ([ref] if ref is not None else [])) if (prev or ref is not None) else None
        m = checkpoint("stage end", stage_end=True)
        st_state["stage_ends"].append({"stage": st["name"], "seen": st_state["seen"], "metric": m})
        st_state["next_ckpt_seen"] = (st_state["seen"] // every + 1) * every
        rule = plan.get("stop_rule")
        if rule and prev_best is not None and i >= int(rule.get("from_stage_index", 1)):
            gain = prev_best - m
            say(f"stage {st['name']} end: metric {m:.6f}, best before {prev_best:.6f}, gain {gain:.6f} (minimum {rule['min_improve']})")
            if gain < float(rule["min_improve"]):
                st_state["stop_reason"] = f"plateau: stage {st['name']} gained {gain:.6f} < {rule['min_improve']}"
        st_state["stage"] += 1
        st_state["stage_step"] = 0
        save()
        t_mark, seen_mark = time.time(), st_state["seen"]
    if not st_state["stop_reason"]:
        st_state["stop_reason"] = "plan complete"
    final_reason = st_state["stop_reason"]
    resumable = final_reason.startswith(("STOP flag", "--max-pres", "--max-minutes"))
    if resumable:
        st_state["stop_reason"] = ""          # a later --resume continues the plan
        save()
    else:
        save()
    with open(os.path.join(a.run_dir, "status.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"train_state": st_state, "backend": backend, "pid": os.getpid(), "plan": a.plan, "exit": final_reason,
                   "max_hot": guard.max_hot, "max_memj": guard.max_mj,
                   "index_sha256": idx_hash.hexdigest() if idx_hash else None}, f, indent=1, sort_keys=True)
    say(f"EXIT {final_reason}: seen {st_state['seen']} best {st_state['best']} holds {guard.holds} "
        f"({guard.hold_seconds:.0f}s) max hot/memj {guard.max_hot:.0f}/{guard.max_mj:.0f} "
        f"wall {(time.time() - t_run) / 60:.1f} min" + (f" index_sha256 {idx_hash.hexdigest()}" if idx_hash else ""))


# ---------------------------------------------------------------- score / selfcheck

FINAL_TEST_TAG = "final_test"


def cmd_score(a):
    if FINAL_TEST_TAG in os.path.basename(a.pos).lower():
        if not a.final_test_unlock:
            raise SystemExit("refused: this is the final-test set; it is scored once, with --final-test-unlock")
        with open(os.path.join(os.path.dirname(os.path.abspath(a.pos)), "FINAL_TEST_ACCESS.log"), "a", encoding="utf-8",
                  newline="\n") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} score net {a.net} pos {a.pos}\n")
    dev = torch.device("cuda")
    boards, score, meta, _ = load_fpos_gpu([a.pos], dev, lambda m: None)
    hce = load_hce_gpu([a.hce], dev) if a.hce else None
    res = score_int(a.net, boards, score, meta, dev, hce=hce)
    res.update({"net": a.net, "net_md5": hashlib.md5(open(a.net, "rb").read()).hexdigest(), "pos": a.pos, "name": a.name})
    print(json.dumps(res, sort_keys=True))
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=1, sort_keys=True)


def cmd_selfcheck(a):
    dev = torch.device("cuda")
    out = {}
    n = a.rows
    data = fb.read_fpos(a.pos, None, n)
    n = data["n"]
    boards = np.fromfile(a.pos, np.uint8, n * 32, offset=16).reshape(n, 32)
    total = fpos_header(a.pos)
    meta_np = np.fromfile(a.pos, np.uint8, n, offset=16 + 34 * total)
    score_np = np.fromfile(a.pos, "<i2", n, offset=16 + 32 * total)
    cfg = {"king_buckets": 8, "mirror": True, "king_map": v3.king_layout(8), "output_map": v3.output_layout(8),
           "output_buckets": 8, "hidden": 512, "eval_scale": 400, "residual": False, "factorizer": True, "seed": 1,
           "init_scale": 0.02, "blend": 0.6}
    T = Tables(cfg, dev)
    bt, mt, st_ = torch.from_numpy(boards).to(dev), torch.from_numpy(meta_np).to(dev), torch.from_numpy(score_np).to(dev)
    # 1. features against FB2's numpy reference
    bad = 0
    stats = {"stm_black": 0, "kb_white": set(), "kb_black": set(), "ob": set(), "mirror_w": set(), "mirror_b": set()}
    for s in range(0, n, 20000):
        us_ref, them_ref, ob_ref = fb.batch_features(data["codes"][s:s + 20000], data["meta"][s:s + 20000], cfg)
        us_white, wi, bi, ob, phase = features(bt[s:s + 20000], mt[s:s + 20000], T)
        stm_b = (data["meta"][s:s + 20000] & 1).astype(bool)
        wi_n, bi_n = wi.cpu().numpy().astype(np.int64), bi.cpu().numpy().astype(np.int64)
        us_g = np.where(stm_b[:, None], bi_n, wi_n)
        th_g = np.where(stm_b[:, None], wi_n, bi_n)

        def canon(x64):
            x = np.where(x64 == T.nf, -1, x64)
            return -np.sort(-x, axis=1)[:, :SLOTS]
        bad += int((canon(us_ref) != -np.sort(-us_g, axis=1)).any(axis=1).sum())
        bad += int((canon(them_ref) != -np.sort(-th_g, axis=1)).any(axis=1).sum())
        bad += int((ob_ref != ob.cpu().numpy()).sum())
        bad += int(((1.0 - stm_b.astype(np.float32)) != us_white.cpu().numpy()).sum())
        stats["stm_black"] += int(stm_b.sum())
        stats["kb_white"] |= set((wi_n.max(axis=1) // 768).tolist())
        stats["kb_black"] |= set((bi_n.max(axis=1) // 768).tolist())
        stats["ob"] |= set(ob_ref.tolist())
    out["features_rows"] = n
    out["features_mismatches"] = bad
    out["coverage"] = {"stm_black_rows": stats["stm_black"], "stm_white_rows": n - stats["stm_black"],
                       "king_buckets_white": sorted(stats["kb_white"]), "king_buckets_black": sorted(stats["kb_black"]),
                       "output_buckets": sorted(stats["ob"])}
    # 2. triton against plain (forward and every gradient) on the checkpoint's weights
    if a.ckpt:
        ck = torch.load(a.ckpt, map_location="cpu", weights_only=False)
        mcfg = ck["cfg"]
        model = fb.build_model(mcfg, torch)
        model.load_state_dict(ck["state"])
        model = model.to(dev)
        ok, why = load_kernels()
        out["triton_import"] = why
        if ok:
            ok2, why2 = KER.triton_usable(dev)
            out["triton_probe"] = why2
            Tm = Tables(mcfg, dev)
            B = 8192
            us_white, wi, bi, ob, phase = features(bt[:B], mt[:B], Tm)
            teacher, res = targets(st_[:B], mt[:B])
            grads = {}
            outs = {}
            for name, f in (("triton", forward_triton), ("plain", forward_plain)):
                model.zero_grad(set_to_none=True)
                cp = f(model, mcfg, us_white, wi, bi, ob, Tm)
                loss = ((torch.sigmoid(cp * (K_SIG / 400.0)) - (0.6 * teacher + 0.4 * res)) ** 2).mean()
                loss.backward()
                outs[name] = (cp.detach(), float(loss))
                grads[name] = {k: p.grad.detach().clone() for k, p in model.named_parameters()}
            out["triton_vs_plain_cp_max_abs"] = float((outs["triton"][0] - outs["plain"][0]).abs().max())
            out["triton_vs_plain_loss"] = [outs["triton"][1], outs["plain"][1]]
            rel = {}
            for k in grads["plain"]:
                ref = float(grads["plain"][k].abs().max())
                rel[k] = float((grads["triton"][k] - grads["plain"][k]).abs().max()) / max(ref, 1e-12)
            out["triton_vs_plain_grad_rel_max"] = rel
            out["triton_ok"] = bool(ok2 and out["triton_vs_plain_cp_max_abs"] < 0.02 and max(rel.values()) < 1e-3)
            # float against integer on the exported weights
            if a.net_out:
                export_cpu(model, mcfg, a.net_out)
                inet = IntNet(a.net_out, dev)
                with torch.no_grad():
                    cpi = forward_int(inet, us_white, wi, bi, ob).to(torch.float64)
                    cq = forward_plain(model, mcfg, us_white, wi, bi, ob, Tm, quant=True).to(torch.float64).clamp(-30000, 30000)
                    cf = forward_plain(model, mcfg, us_white, wi, bi, ob, Tm, quant=False).to(torch.float64).clamp(-30000, 30000)
                out["fakequant_float_vs_int_cp"] = {"max": float((cq - cpi).abs().max()), "mean": float((cq - cpi).abs().mean())}
                out["pure_float_vs_int_cp"] = {"max": float((cf - cpi).abs().max()), "mean": float((cf - cpi).abs().mean())}
    # 3. integer scorer against FB2's numpy scorer
    if a.net:
        g = score_int(a.net, bt, st_, mt, dev)
        full = fb.read_fpos(a.pos, None, n)
        ref = fb.score_net_numpy(v3.read_net(a.net), full, False, phases=True)
        out["int_scorer_gpu"] = {k: g[k] for k in ("mse_b0.6", "mse_b0.8", "mse_b1.0")}
        out["int_scorer_numpy"] = {k: ref[k] for k in ("mse_b0.6", "mse_b0.8", "mse_b1.0")}
        out["int_scorer_max_abs_diff"] = max(abs(g[k] - ref[k]) for k in ("mse_b0.6", "mse_b0.8", "mse_b1.0"))
        out["phase_rows_equal"] = g["phase_rows"] == ref["phase_rows"]
    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1, sort_keys=True, default=str)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("--plan", required=True)
    t.add_argument("--run-dir", required=True)
    t.add_argument("--resume", action="store_true")
    t.add_argument("--backend", choices=["triton", "plain"], default="triton")
    t.add_argument("--no-fallback", action="store_true")
    t.add_argument("--no-guard", action="store_true")
    t.add_argument("--max-pres", type=int, default=0)
    t.add_argument("--max-minutes", type=float, default=0.0)
    t.add_argument("--hash-indices", action="store_true")
    t.add_argument("--log-every", type=int, default=2000)
    t.set_defaults(func=cmd_train)
    s = sub.add_parser("score")
    s.add_argument("--net", required=True)
    s.add_argument("--pos", required=True)
    s.add_argument("--hce")
    s.add_argument("--name", default="")
    s.add_argument("--out", default="")
    s.add_argument("--final-test-unlock", action="store_true")
    s.set_defaults(func=cmd_score)
    c = sub.add_parser("selfcheck")
    c.add_argument("--pos", required=True)
    c.add_argument("--ckpt")
    c.add_argument("--net")
    c.add_argument("--net-out", default="")
    c.add_argument("--rows", type=int, default=100000)
    c.add_argument("--out", default="")
    c.set_defaults(func=cmd_selfcheck)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
