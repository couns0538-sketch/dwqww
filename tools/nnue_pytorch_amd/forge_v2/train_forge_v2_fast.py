"""R7 J1: train Forge's stand-alone v2 net (FORGENN2) on the fast AMD path, and benchmark it.

Licence: GPL-3.0 (tool code next to the nnue-pytorch AMD port; it imports nnue-pytorch's data loader).
Derived from Grok Bot's F:\\nnue_pytorch\\forge_tools\\train_forge_v2.py (read only; same model, loss,
optimizer, clipping and export), with these changes:
  --backend triton : forge_v2_kernels.ForgeV2FT (one Triton kernel for both perspectives: gather-sum,
                     us/them mix, clamp, square; the K32H3 -> Forge remap is done inside the kernel; the
                     backward scatters with fp32 atomics) and the output layer as x @ w2^T + bucket gather.
  --backend plain  : Grok Bot's path (F.embedding_bag over the remapped indices with a zero padding row,
                     x * w2[bucket] summed), kept for the A/B.
  --fused-adam 1   : torch.optim.Adam(fused=True).
  --mode loader    : data path only (fetch + H2D + remap), no model.
  --mode synthetic : one real batch kept on the GPU, train steps only (GPU-bound ceiling).
Safety caps of this PC (R7 rules): --batch <= 8192, --threads (loader workers) <= 2, one process.
Run it under tools/nnue_pytorch_amd/guard/guard_exec.py (aborts below 7 GB free RAM).

Model (include/forge/nnue_v2.hpp): 32 king buckets x 768 inputs, horizontal mirror (own king to files a-d),
hidden H, SCReLU(stm) | SCReLU(other), one linear output per output bucket (default map
min(N - 1, (pieces - 2) * N // 32)), cp = out * 400 / 2.25.
K32H3 idx = osq + (type * 2 + rel) * 64 + (state * 32 + kb) * 768 (osq: king on files e-h);
Forge idx = kb * 768 + (rel * 6 + type) * 64 + (osq ^ 7) (state dropped, Forge mirrors the king to a-d).
"""
import argparse
import importlib.util
import json
import math
import os
import sys
import time

NNUE_REPO = os.environ.get("NNUE_REPO", r"F:\opus_scratch\r6\nnue-pytorch-amd")
sys.path.insert(0, NNUE_REPO)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402

import forge_v2_kernels as K  # noqa: E402

FORGE_WRITER = os.environ.get(
    "FORGE_V2_WRITER", r"D:\grok-pc-data\dwqww\.claude\worktrees\opus-r7-nps\tools\nnue\forge_nnue_v2.py")
KB = [-1, -1, -1, -1, 31, 30, 29, 28, -1, -1, -1, -1, 27, 26, 25, 24, -1, -1, -1, -1, 23, 22, 21, 20,
      -1, -1, -1, -1, 19, 18, 17, 16, -1, -1, -1, -1, 15, 14, 13, 12, -1, -1, -1, -1, 11, 10, 9, 8,
      -1, -1, -1, -1, 7, 6, 5, 4, -1, -1, -1, -1, 3, 2, 1, 0]
NKB, INP = 32, 768
NF = NKB * INP
PAD = NF  # plain backend: padding row (kept zero)
QMAX = 32767 / 4096.0
MAX_BATCH, MAX_THREADS = 8192, 2


def load_writer():
    spec = importlib.util.spec_from_file_location("forge_nnue_v2", FORGE_WRITER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def king_map():
    return [KB[k] if (k & 7) >= 4 else KB[k ^ 7] for k in range(64)]


def remap_table():
    """K32H3 index -> Forge index (int64, 3 * 32 * 768 entries)."""
    i = torch.arange(3 * NKB * INP, dtype=torch.int64)
    bucket = i // INP
    kb = bucket % NKB
    plane = i % INP
    p_idx = plane // 64
    osq = plane % 64
    typ = p_idx // 2
    rel = p_idx % 2
    return kb * INP + (rel * 6 + typ) * 64 + (osq ^ 7)


def plain_lut(device):  # index -1 -> last entry -> PAD row
    return torch.cat([remap_table(), torch.tensor([PAD])]).to(device)


def triton_lut(device):  # index -1 -> last entry -> -1 (empty slot)
    return torch.cat([remap_table(), torch.tensor([-1])]).to(torch.int32).to(device)


def output_bucket(pc, nob):
    return torch.clamp((pc - 2).clamp(min=0) * nob // 32, max=nob - 1)


class ForgeV2Plain(torch.nn.Module):
    """Grok Bot's model, unchanged (w1 has a zero padding row at index NF)."""

    def __init__(self, hidden, nob):
        super().__init__()
        self.hidden, self.nob = hidden, nob
        self.w1 = torch.nn.Parameter(torch.empty(NF + 1, hidden).uniform_(-0.06, 0.06))
        with torch.no_grad():
            self.w1[PAD].zero_()
        self.b1 = torch.nn.Parameter(torch.full((hidden,), 0.1))
        self.w2 = torch.nn.Parameter(torch.empty(nob, 2 * hidden).uniform_(-0.1, 0.1))
        self.b2 = torch.nn.Parameter(torch.zeros(nob))

    def acc(self, idx):
        return F.embedding_bag(idx, self.w1, mode="sum", padding_idx=PAD) + self.b1

    def forward(self, us, wi, bi, pc):
        aw, ab = self.acc(wi), self.acc(bi)
        ours = us * aw + (1 - us) * ab
        theirs = us * ab + (1 - us) * aw
        x = torch.cat([ours.clamp(0, 1) ** 2, theirs.clamp(0, 1) ** 2], dim=1)
        ob = output_bucket(pc, self.nob)
        return (x * self.w2[ob]).sum(1) + self.b2[ob]

    @torch.no_grad()
    def clip(self):
        for p in (self.w1, self.b1, self.w2, self.b2):
            p.clamp_(-QMAX, QMAX)
        self.w1[PAD].zero_()

    def export_w1(self):
        return self.w1[:NF]


class ForgeV2Triton(torch.nn.Module):
    """Same net; w1 has no padding row (empty slots are -1 and skipped by the kernel)."""

    def __init__(self, hidden, nob):
        super().__init__()
        self.hidden, self.nob = hidden, nob
        self.w1 = torch.nn.Parameter(torch.empty(NF, hidden).uniform_(-0.06, 0.06))
        self.b1 = torch.nn.Parameter(torch.full((hidden,), 0.1))
        self.w2 = torch.nn.Parameter(torch.empty(nob, 2 * hidden).uniform_(-0.1, 0.1))
        self.b2 = torch.nn.Parameter(torch.zeros(nob))

    def forward(self, us, wi, bi, pc, lut):
        x = K.ForgeV2FT.apply(us, wi, bi, lut, self.w1, self.b1)
        ob = output_bucket(pc, self.nob).view(-1, 1)
        return (x @ self.w2.t()).gather(1, ob).view(-1) + self.b2[ob.view(-1)]

    @torch.no_grad()
    def clip(self):
        for p in (self.w1, self.b1, self.w2, self.b2):
            p.clamp_(-QMAX, QMAX)

    def export_w1(self):
        return self.w1


def export(model, path):
    import numpy as np
    V2 = load_writer()

    def q(t):
        return np.rint(t.detach().float().cpu().numpy() * 4096.0).clip(-32768, 32767).astype(np.int16)

    w1 = q(model.export_w1()).reshape(NKB, INP, model.hidden)
    return V2.write_v2(path, hidden=model.hidden, king_buckets=NKB, residual=False, mirror=True,
                       king_map=king_map(), w1=w1, b1=q(model.b1), w2=q(model.w2), b2=q(model.b2),
                       output_buckets=model.nob, output_map=V2.output_layout(model.nob))


def to_device(b, backend, lut, dev, pinned=False):
    # pinned: copy into pinned host memory, then a non-blocking H2D copy (the host does not wait for the GPU)
    us, them, wi, bi, outcome, score, pc, qb = b.contents.get_tensors(dev, use_pinned_memory=pinned)
    if backend == "plain":
        wi = lut[wi.long()]
        bi = lut[bi.long()]
    # triton: raw int32 loader indices, remapped inside the kernel
    return us.float(), wi, bi, outcome.float().view(-1), score.float().view(-1), pc.long()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--backend", choices=["plain", "triton"], default="triton")
    ap.add_argument("--mode", choices=["train", "loader", "synthetic"], default="train")
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--ob", type=int, default=8)
    ap.add_argument("--batch", type=int, default=8192)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--warmup", type=int, default=30, help="steps excluded from the timed window")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam", type=float, default=0.75, help="weight of the score target vs game result")
    ap.add_argument("--threads", type=int, default=2, help="loader worker threads")
    ap.add_argument("--fused-adam", type=int, default=0)
    ap.add_argument("--compile", type=int, default=0, help="torch.compile the loss/output part")
    ap.add_argument("--pinned", type=int, default=0, help="pinned host memory + non-blocking H2D copies")
    ap.add_argument("--inflight", type=int, default=3,
                    help="with --pinned: at most this many steps queued ahead of the GPU (bounds pinned host memory)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--device", default="auto", help="auto | cuda | cpu (cpu: loader-only scaling runs)")
    ap.add_argument("--out", default="", help="output prefix (.pt and .fnn2); empty = no export")
    ap.add_argument("--json", default="", help="write a result summary here")
    ap.add_argument("--log-every", type=int, default=50)
    a = ap.parse_args()
    if a.batch > MAX_BATCH or a.threads > MAX_THREADS or a.threads < 1:
        sys.exit(f"refused: batch {a.batch} (max {MAX_BATCH}) / threads {a.threads} (1..{MAX_THREADS}) "
                 "are this PC's safety caps while the live trainer runs")
    torch.manual_seed(a.seed)
    from data_loader import DataloaderSkipConfig
    from data_loader import stream as st
    dev = torch.device(a.device if a.device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu"))
    info = {"args": vars(a), "device": str(dev), "torch": torch.__version__, "hip": torch.version.hip,
            "loader_lib": os.environ.get("NNUE_DATA_LOADER_LIB", "(default build/ glob)")}
    if a.backend == "triton" and a.mode != "loader":
        ok, why = K.triton_usable(dev)
        info["triton_probe"] = why
        if not ok:
            sys.exit(f"Triton backend unusable: {why}")
    lut = plain_lut(dev) if a.backend == "plain" else triton_lut(dev)
    model = None
    if a.mode != "loader":
        model = (ForgeV2Plain if a.backend == "plain" else ForgeV2Triton)(a.hidden, a.ob).to(dev)
        kw = {"fused": True} if a.fused_adam else {}
        opt = torch.optim.Adam(model.parameters(), lr=a.lr, **kw)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.steps, eta_min=a.lr * 0.05)

    def loss_fn(out, score, outcome):
        target = a.lam * torch.sigmoid(score * 2.25 / 400.0) + (1 - a.lam) * outcome
        return ((torch.sigmoid(out) - target) ** 2).mean()

    if a.compile:
        loss_fn = torch.compile(loss_fn, dynamic=False)

    def forward(us, wi, bi, pc):
        return model(us, wi, bi, pc) if a.backend == "plain" else model(us, wi, bi, pc, lut)

    cfg = DataloaderSkipConfig(filtered=False, wld_filtered=False, random_fen_skipping=0,
                               early_fen_skipping=-1, soft_early_fen_skipping=0)
    s = st.create_sparse_batch_stream(b"K32H3", a.threads, [a.data], a.batch, True, cfg)
    fixed = None
    if a.mode == "synthetic":
        b = st.fetch_next_sparse_batch(s)
        fixed = to_device(b, a.backend, lut, dev)
        st.destroy_sparse_batch(b)
    n_timed = 0
    run = None
    t_start = None
    losses = []
    inflight = []
    t_wall0 = time.time()
    for step in range(1, a.steps + 1):
        if step == a.warmup + 1:
            if dev.type == "cuda":
                torch.cuda.synchronize()
            t_start = time.perf_counter()
        if fixed is None:
            b = st.fetch_next_sparse_batch(s)
            us, wi, bi, outcome, score, pc = to_device(b, a.backend, lut, dev, bool(a.pinned))
            st.destroy_sparse_batch(b)
        else:
            us, wi, bi, outcome, score, pc = fixed
        if a.mode != "loader":
            out = forward(us, wi, bi, pc)
            loss = loss_fn(out, score, outcome)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            model.clip()
        if a.pinned and dev.type == "cuda":
            ev = torch.cuda.Event()
            ev.record()
            inflight.append(ev)
            if len(inflight) > a.inflight:
                inflight.pop(0).synchronize()
        if step > a.warmup:
            n_timed += us.shape[0]
        if a.mode != "loader" and (step % a.log_every == 0 or step == a.steps):
            lv = loss.item()
            run = lv if run is None else 0.9 * run + 0.1 * lv
            losses.append([step, lv])
            el = time.perf_counter() - t_start if t_start else float("nan")
            rate = n_timed / el if t_start and el > 0 else float("nan")
            print(f"step {step} loss {lv:.5f} ema {run:.5f} timed_pos {n_timed} {rate:.0f} pos/s", flush=True)
    if dev.type == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - t_start
    st.destroy_sparse_batch_stream(s)
    info.update({"timed_steps": a.steps - a.warmup, "timed_positions": n_timed, "timed_seconds": elapsed,
                 "pos_per_s": n_timed / elapsed, "wall_seconds": time.time() - t_wall0, "losses": losses})
    if dev.type == "cuda":
        info["gpu_peak_alloc_mb"] = torch.cuda.max_memory_allocated() / 2 ** 20
    print(f"RESULT backend={a.backend} mode={a.mode} batch={a.batch} threads={a.threads} "
          f"fused_adam={a.fused_adam} compile={a.compile} pinned={a.pinned}: {info['pos_per_s']:.0f} pos/s over "
          f"{a.steps - a.warmup} steps ({elapsed:.2f} s)", flush=True)
    if a.out and model is not None:
        torch.save({"state": model.state_dict(), "hidden": a.hidden, "ob": a.ob, "backend": a.backend},
                   a.out + ".pt")
        ck = export(model, a.out + ".fnn2")
        info["export"] = {"fnn2": a.out + ".fnn2", "fnv1a": f"{ck:016x}"}
        print(f"exported {a.out}.fnn2 checksum {ck:016x}", flush=True)
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(info, f, indent=1)


if __name__ == "__main__":
    main()
