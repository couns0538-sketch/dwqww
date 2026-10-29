"""R6 Triton-on-ROCm-Windows smoke: add, fp32 atomic_add, 2-D gather.  Seconds of GPU time."""
import os
import sys
import time
import traceback

import torch

torch.set_num_threads(3)
print("torch", torch.__version__, "hip", torch.version.hip, torch.cuda.get_device_name(0), flush=True)
import triton
import triton.language as tl

print("triton", triton.__version__, flush=True)


@triton.jit
def add_k(x, y, o, n, B: tl.constexpr):
    p = tl.program_id(0) * B + tl.arange(0, B)
    m = p < n
    tl.store(o + p, tl.load(x + p, mask=m) + tl.load(y + p, mask=m), mask=m)


@triton.jit
def atomic_k(idx, val, out, n, B: tl.constexpr):
    p = tl.program_id(0) * B + tl.arange(0, B)
    m = p < n
    i = tl.load(idx + p, mask=m, other=0)
    v = tl.load(val + p, mask=m, other=0.0)
    tl.atomic_add(out + i, v, mask=m, sem="relaxed")


@triton.jit
def gather_k(idx, w, o, A: tl.constexpr, L: tl.constexpr, BC: tl.constexpr):
    b = tl.program_id(0)
    c = tl.program_id(1) * BC + tl.arange(0, BC)
    k = tl.arange(0, A)
    ii = tl.load(idx + b * A + k)
    ok = ii >= 0
    rows = tl.where(ok, ii, 0).to(tl.int64)
    t = tl.load(w + rows[:, None] * L + c[None, :], mask=ok[:, None], other=0.0)
    tl.store(o + b * L + c, tl.sum(t, axis=0))


ok_all = True
try:
    a = torch.randn(4096, device="cuda")
    b = torch.randn(4096, device="cuda")
    o = torch.empty_like(a)
    add_k[(4,)](a, b, o, 4096, B=1024)
    torch.cuda.synchronize()
    print("add OK maxerr", (o - (a + b)).abs().max().item(), flush=True)
except Exception:
    ok_all = False
    print("ADD_FAIL")
    traceback.print_exc()

try:
    n = 1 << 16
    idx = torch.randint(0, 97, (n,), device="cuda", dtype=torch.int32)
    val = torch.randn(n, device="cuda")
    out = torch.zeros(97, device="cuda")
    atomic_k[(n // 1024,)](idx, val, out, n, B=1024)
    ref = torch.zeros(97, device="cuda").index_add_(0, idx.long(), val)
    torch.cuda.synchronize()
    print("atomic_add OK maxerr", (out - ref).abs().max().item(), flush=True)
except Exception:
    ok_all = False
    print("ATOMIC_FAIL")
    traceback.print_exc()

try:
    A, L, B = 32, 256, 512
    w = torch.randn(5000, L, device="cuda")
    idx = torch.randint(0, 5000, (B, A), device="cuda", dtype=torch.int32)
    idx[:, 28:] = -1
    o = torch.empty(B, L, device="cuda")
    gather_k[(B, L // 64)](idx, w, o, A=A, L=L, BC=64)
    m = (idx >= 0).float()
    ref = (w[idx.clamp(min=0).long()] * m[:, :, None]).sum(1)
    torch.cuda.synchronize()
    print("gather OK maxerr", (o - ref).abs().max().item(), flush=True)
except Exception:
    ok_all = False
    print("GATHER_FAIL")
    traceback.print_exc()

print("ALL_OK" if ok_all else "SOME_FAIL", flush=True)
