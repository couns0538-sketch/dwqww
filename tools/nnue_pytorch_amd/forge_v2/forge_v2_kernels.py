"""Triton kernels for Forge's stand-alone v2 net (FORGENN2): king-bucketed HalfKA-style feature
transformer with SCReLU, as used by train_forge_v2_fast.py (R7 J1).

Licence: GPL-3.0. This is tool code of the nnue-pytorch AMD port (tools/nnue_pytorch_amd/, derived from
the R6 Triton port of nnue-pytorch's CuPy feature-transformer kernels). It never goes into Forge
src/, include/ or tests/.

Net (include/forge/nnue_v2.hpp, read only):
  acc_p   = b1 + sum of W[f] over the active features f of perspective p   (p = White, Black)
  ours    = acc_stm, theirs = acc_other
  out     = b2[ob] + sum_j clamp(ours_j, 0, 1)^2 * w2[ob, j] + clamp(theirs_j, 0, 1)^2 * w2[ob, H + j]

Kernels (one program = one position x BLOCK_C columns):
  forward : x[b, :H] = clamp(ours, 0, 1)^2, x[b, H:] = clamp(theirs, 0, 1)^2 and the pre-activations
            pre[b, 0] = ours, pre[b, 1] = theirs (saved for the backward pass).
  backward: g_o = gx[b, :H] * 2 * clamp(ours) where 0 <= ours <= 1, else 0 (torch's clamp gradient,
            boundaries included), same for theirs; g_w = u * g_o + (1 - u) * g_t (u = 1: White to move),
            g_b = (1 - u) * g_o + u * g_t; W rows get fp32 atomics, the bias gradient is summed over
            POS positions in registers first (one atomic per column and program).
Feature indices are the loader's raw K32H3 indices (int32, -1 = empty slot); the K32H3 -> Forge remap
(a 73,729-entry int32 table, last entry -1) is applied inside both kernels, so no index tensor is
rewritten on the host or the GPU.
"""

import os

import torch
import triton
import triton.language as tl
from torch import autograd


def _env_int(name, default):
    v = os.environ.get(name, "")
    return int(v) if v.strip() else default


@triton.jit
def _fwd_kernel(us_ptr, widx_ptr, bidx_ptr, lut_ptr, w_ptr, b_ptr, x_ptr, pre_ptr,
                A: tl.constexpr, H: tl.constexpr, KC: tl.constexpr, BLOCK_C: tl.constexpr):
    pid_b = tl.program_id(0).to(tl.int64)
    cols = tl.program_id(1) * BLOCK_C + tl.arange(0, BLOCK_C)
    cmask = cols < H
    bias = tl.load(b_ptr + cols, mask=cmask, other=0.0)
    aw = bias
    ab = bias
    for k0 in tl.static_range(0, A, KC):
        ks = k0 + tl.arange(0, KC)
        km = ks < A
        rw = tl.load(widx_ptr + pid_b * A + ks, mask=km, other=-1)
        rb = tl.load(bidx_ptr + pid_b * A + ks, mask=km, other=-1)
        fw = tl.load(lut_ptr + tl.where(rw >= 0, rw, 0), mask=rw >= 0, other=-1)
        fb = tl.load(lut_ptr + tl.where(rb >= 0, rb, 0), mask=rb >= 0, other=-1)
        vw = fw >= 0
        vb = fb >= 0
        pw = w_ptr + (tl.where(vw, fw, 0).to(tl.int64) * H)[:, None] + cols[None, :]
        pb = w_ptr + (tl.where(vb, fb, 0).to(tl.int64) * H)[:, None] + cols[None, :]
        aw += tl.sum(tl.load(pw, mask=vw[:, None] & cmask[None, :], other=0.0), axis=0)
        ab += tl.sum(tl.load(pb, mask=vb[:, None] & cmask[None, :], other=0.0), axis=0)
    u = tl.load(us_ptr + pid_b)
    t = 1.0 - u
    ours = u * aw + t * ab
    theirs = u * ab + t * aw
    co = tl.minimum(tl.maximum(ours, 0.0), 1.0)
    ct = tl.minimum(tl.maximum(theirs, 0.0), 1.0)
    xo = x_ptr + pid_b * (2 * H) + cols
    tl.store(xo, co * co, mask=cmask)
    tl.store(xo + H, ct * ct, mask=cmask)
    po = pre_ptr + pid_b * (2 * H) + cols
    tl.store(po, ours, mask=cmask)
    tl.store(po + H, theirs, mask=cmask)


@triton.jit
def _bwd_kernel(us_ptr, widx_ptr, bidx_ptr, lut_ptr, gx_ptr, pre_ptr, gw_ptr, gb_ptr, batch_size,
                A: tl.constexpr, H: tl.constexpr, KC: tl.constexpr, BLOCK_C: tl.constexpr,
                POS: tl.constexpr):
    pid_p = tl.program_id(0)
    cols = tl.program_id(1) * BLOCK_C + tl.arange(0, BLOCK_C)
    cmask = cols < H
    gbias = tl.zeros([BLOCK_C], dtype=tl.float32)
    for p in range(POS):
        b = pid_p * POS + p
        if b < batch_size:
            b64 = b.to(tl.int64)
            po = pre_ptr + b64 * (2 * H) + cols
            ours = tl.load(po, mask=cmask, other=0.0)
            theirs = tl.load(po + H, mask=cmask, other=0.0)
            go = gx_ptr + b64 * (2 * H) + cols
            gxo = tl.load(go, mask=cmask, other=0.0)
            gxt = tl.load(go + H, mask=cmask, other=0.0)
            g_o = tl.where((ours >= 0.0) & (ours <= 1.0), 2.0 * tl.minimum(tl.maximum(ours, 0.0), 1.0) * gxo, 0.0)
            g_t = tl.where((theirs >= 0.0) & (theirs <= 1.0), 2.0 * tl.minimum(tl.maximum(theirs, 0.0), 1.0) * gxt, 0.0)
            u = tl.load(us_ptr + b64)
            t = 1.0 - u
            g_w = u * g_o + t * g_t
            g_b = t * g_o + u * g_t
            gbias += g_w + g_b
            nz_w = cmask & (g_w != 0.0)
            nz_b = cmask & (g_b != 0.0)
            for k0 in tl.static_range(0, A, KC):
                ks = k0 + tl.arange(0, KC)
                km = ks < A
                rw = tl.load(widx_ptr + b64 * A + ks, mask=km, other=-1)
                rb = tl.load(bidx_ptr + b64 * A + ks, mask=km, other=-1)
                fw = tl.load(lut_ptr + tl.where(rw >= 0, rw, 0), mask=rw >= 0, other=-1)
                fb = tl.load(lut_ptr + tl.where(rb >= 0, rb, 0), mask=rb >= 0, other=-1)
                vw = fw >= 0
                vb = fb >= 0
                pw = gw_ptr + (tl.where(vw, fw, 0).to(tl.int64) * H)[:, None] + cols[None, :]
                pb = gw_ptr + (tl.where(vb, fb, 0).to(tl.int64) * H)[:, None] + cols[None, :]
                tl.atomic_add(pw, tl.broadcast_to(g_w[None, :], [KC, BLOCK_C]),
                              mask=vw[:, None] & nz_w[None, :], sem="relaxed")
                tl.atomic_add(pb, tl.broadcast_to(g_b[None, :], [KC, BLOCK_C]),
                              mask=vb[:, None] & nz_b[None, :], sem="relaxed")
    tl.atomic_add(gb_ptr + cols, gbias, mask=cmask & (gbias != 0.0), sem="relaxed")


def _pow2_at_most(n, cap):
    p = 1
    while p * 2 <= min(n, cap):
        p *= 2
    return p


def _cfg(active, hidden):
    bc = _env_int("FORGE_V2_BLOCK_C", _pow2_at_most(hidden, 128))
    kc = _env_int("FORGE_V2_KC", min(16, triton.next_power_of_2(active)))
    return bc, kc, _env_int("FORGE_V2_WARPS", 4), _env_int("FORGE_V2_POS", 8)


@torch.compiler.disable
def ft_forward(us, widx, bidx, lut, weight, bias):
    batch, active = widx.shape
    hidden = weight.shape[1]
    x = torch.empty(batch, 2 * hidden, dtype=torch.float32, device=weight.device)
    pre = torch.empty(batch, 2 * hidden, dtype=torch.float32, device=weight.device)
    if batch == 0:
        return x, pre
    bc, kc, warps, _ = _cfg(active, hidden)
    _fwd_kernel[(batch, triton.cdiv(hidden, bc))](us, widx, bidx, lut, weight, bias, x, pre,
                                                   A=active, H=hidden, KC=kc, BLOCK_C=bc, num_warps=warps)
    return x, pre


@torch.compiler.disable
def ft_backward(us, widx, bidx, lut, grad_x, pre, num_inputs):
    batch, active = widx.shape
    hidden = pre.shape[1] // 2
    gw = torch.zeros(num_inputs, hidden, dtype=torch.float32, device=grad_x.device)
    gb = torch.zeros(hidden, dtype=torch.float32, device=grad_x.device)
    if batch == 0:
        return gw, gb
    bc, kc, warps, pos = _cfg(active, hidden)
    _bwd_kernel[(triton.cdiv(batch, pos), triton.cdiv(hidden, bc))](
        us, widx, bidx, lut, grad_x, pre, gw, gb, batch,
        A=active, H=hidden, KC=kc, BLOCK_C=bc, POS=pos, num_warps=warps)
    return gw, gb


def _i32(t):
    return (t if t.dtype == torch.int32 else t.to(torch.int32)).contiguous()


class ForgeV2FT(autograd.Function):
    """x = [clamp(ours,0,1)^2 | clamp(theirs,0,1)^2] from raw loader indices; gradients for W and b1."""

    @staticmethod
    def forward(ctx, us, widx, bidx, lut, weight, bias):
        us = us.reshape(-1).to(torch.float32).contiguous()
        widx, bidx, lut = _i32(widx), _i32(bidx), _i32(lut)
        assert widx.shape == bidx.shape and us.numel() == widx.shape[0]
        assert weight.dtype == torch.float32 and bias.dtype == torch.float32
        x, pre = ft_forward(us, widx, bidx, lut, weight.contiguous(), bias.contiguous())
        ctx.save_for_backward(us, widx, bidx, lut, pre)
        ctx.num_inputs = weight.shape[0]
        return x

    @staticmethod
    def backward(ctx, grad_x):
        us, widx, bidx, lut, pre = ctx.saved_tensors
        gw, gb = ft_backward(us, widx, bidx, lut, grad_x.contiguous(), pre, ctx.num_inputs)
        return None, None, None, None, gw, gb


def triton_usable(device):
    """Run one tiny forward/backward against a torch reference; False (and why) when Triton fails."""
    try:
        g = torch.Generator().manual_seed(1)
        w = torch.randn(10, 16, generator=g).to(device).requires_grad_(True)
        b = torch.randn(16, generator=g).to(device).requires_grad_(True)
        lut = torch.tensor([3, 1, 4, 1, 5, 9, 2, 6, -1], dtype=torch.int32, device=device)
        wi = torch.tensor([[0, 2, -1, -1], [1, 5, 6, -1]], dtype=torch.int32, device=device)
        bi = torch.tensor([[4, -1, -1, -1], [7, 0, -1, -1]], dtype=torch.int32, device=device)
        us = torch.tensor([1.0, 0.0], device=device)
        x = ForgeV2FT.apply(us, wi, bi, lut, w, b)
        ref = reference_x(us, wi, bi, lut, w, b)
        ok = torch.allclose(x, ref, atol=1e-5)
        return ok, ("ok" if ok else "probe mismatch")
    except Exception as e:  # broken Triton install, missing HIP headers, ...
        return False, f"{type(e).__name__}: {e}"


def reference_x(us, widx, bidx, lut, weight, bias):
    """Plain torch reference of the forward pass (same semantics, gather + sum)."""
    lut64 = lut.long()

    def acc(idx):
        f = lut64[idx.long().clamp(min=0)]
        f = torch.where(idx.long() >= 0, f, torch.full_like(f, -1))
        rows = weight[f.clamp(min=0)] * (f >= 0).unsqueeze(-1).to(weight.dtype)
        return rows.sum(1) + bias

    aw, ab = acc(widx), acc(bidx)
    u = us.reshape(-1, 1).to(weight.dtype)
    ours = u * aw + (1 - u) * ab
    theirs = u * ab + (1 - u) * aw
    return torch.cat([ours.clamp(0, 1) ** 2, theirs.clamp(0, 1) ** 2], dim=1)
