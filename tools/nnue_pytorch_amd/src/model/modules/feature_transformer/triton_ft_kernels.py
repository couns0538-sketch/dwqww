"""Triton kernels for the feature transformer (AMD ROCm and any Triton GPU).

Part of nnue-pytorch, GPL-3.0. Triton re-implementation of the CuPy kernels in
sparse_linear_kernel.py and fused_ft_kernel.py (same math and launch semantics,
written for Triton so they run under ROCm on Windows where CuPy is missing).

Index rows are int32, -1 marks an empty slot.  Every slot with an index >= 0 is
accumulated (the torch fallback's semantics); the extractors pad with -1 at the
end, so this equals the CuPy kernels' early exit on valid batches.

Backward kernels scatter with fp32 atomics like the CUDA kernels; zero
gradients are skipped.  Each backward program handles POS positions so the bias
gradient is reduced in registers before one atomic per column.
"""

import os

import torch
import triton
import triton.language as tl


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "")
    return int(v) if v.strip() else default


@triton.jit
def _sparse_fwd_kernel(
    idx_ptr,
    w_ptr,
    bias_ptr,
    out_ptr,
    A: tl.constexpr,
    N: tl.constexpr,
    KC: tl.constexpr,
    BLOCK_N: tl.constexpr,
):
    pid_b = tl.program_id(0).to(tl.int64)
    cols = tl.program_id(1) * BLOCK_N + tl.arange(0, BLOCK_N)
    cmask = cols < N
    acc = tl.load(bias_ptr + cols, mask=cmask, other=0.0)
    for k0 in tl.static_range(0, A, KC):
        ks = k0 + tl.arange(0, KC)
        ii = tl.load(idx_ptr + pid_b * A + ks, mask=ks < A, other=-1)
        valid = ii >= 0
        rows = tl.where(valid, ii, 0).to(tl.int64) * N
        t = tl.load(
            w_ptr + rows[:, None] + cols[None, :],
            mask=valid[:, None] & cmask[None, :],
            other=0.0,
        )
        acc += tl.sum(t, axis=0)
    tl.store(out_ptr + pid_b * N + cols, acc, mask=cmask)


@triton.jit
def _sparse_bwd_kernel(
    idx_ptr,
    gout_ptr,
    gw_ptr,
    gb_ptr,
    batch_size,
    A: tl.constexpr,
    N: tl.constexpr,
    KC: tl.constexpr,
    BLOCK_N: tl.constexpr,
    POS: tl.constexpr,
):
    pid_p = tl.program_id(0)
    cols = tl.program_id(1) * BLOCK_N + tl.arange(0, BLOCK_N)
    cmask = cols < N
    gb = tl.zeros([BLOCK_N], dtype=tl.float32)
    for p in range(POS):
        b = pid_p * POS + p
        if b < batch_size:
            b64 = b.to(tl.int64)
            g = tl.load(gout_ptr + b64 * N + cols, mask=cmask, other=0.0)
            gb += g
            gmask = cmask & (g != 0.0)
            for k0 in tl.static_range(0, A, KC):
                ks = k0 + tl.arange(0, KC)
                ii = tl.load(idx_ptr + b64 * A + ks, mask=ks < A, other=-1)
                valid = ii >= 0
                rows = tl.where(valid, ii, 0).to(tl.int64) * N
                tl.atomic_add(
                    gw_ptr + rows[:, None] + cols[None, :],
                    tl.broadcast_to(g[None, :], [KC, BLOCK_N]),
                    mask=valid[:, None] & gmask[None, :],
                    sem="relaxed",
                )
    tl.atomic_add(gb_ptr + cols, gb, mask=cmask & (gb != 0.0), sem="relaxed")


@triton.jit
def _fused_fwd_kernel(
    us_ptr,
    them_ptr,
    widx_ptr,
    bidx_ptr,
    w_ptr,
    bias_ptr,
    l0_ptr,
    cl_ptr,
    max_act,
    A: tl.constexpr,
    L1: tl.constexpr,
    HALF: tl.constexpr,
    KC: tl.constexpr,
    BLOCK_C: tl.constexpr,
):
    pid_b = tl.program_id(0).to(tl.int64)
    cols = tl.program_id(1) * BLOCK_C + tl.arange(0, BLOCK_C)
    cmask = cols < HALF
    bias0 = tl.load(bias_ptr + cols, mask=cmask, other=0.0)
    bias1 = tl.load(bias_ptr + HALF + cols, mask=cmask, other=0.0)
    w0 = bias0
    w1 = bias1
    b0 = bias0
    b1 = bias1
    for k0 in tl.static_range(0, A, KC):
        ks = k0 + tl.arange(0, KC)
        km = ks < A
        wi = tl.load(widx_ptr + pid_b * A + ks, mask=km, other=-1)
        bi = tl.load(bidx_ptr + pid_b * A + ks, mask=km, other=-1)
        wv = wi >= 0
        bv = bi >= 0
        wr = tl.where(wv, wi, 0).to(tl.int64) * L1
        br = tl.where(bv, bi, 0).to(tl.int64) * L1
        m_w = wv[:, None] & cmask[None, :]
        m_b = bv[:, None] & cmask[None, :]
        pw = w_ptr + wr[:, None] + cols[None, :]
        pb = w_ptr + br[:, None] + cols[None, :]
        w0 += tl.sum(tl.load(pw, mask=m_w, other=0.0), axis=0)
        w1 += tl.sum(tl.load(pw + HALF, mask=m_w, other=0.0), axis=0)
        b0 += tl.sum(tl.load(pb, mask=m_b, other=0.0), axis=0)
        b1 += tl.sum(tl.load(pb + HALF, mask=m_b, other=0.0), axis=0)

    u = tl.load(us_ptr + pid_b)
    t = tl.load(them_ptr + pid_b)
    l0_w0 = tl.minimum(tl.maximum(u * w0 + t * b0, 0.0), max_act)
    l0_w1 = tl.minimum(tl.maximum(u * w1 + t * b1, 0.0), max_act)
    l0_b0 = tl.minimum(tl.maximum(u * b0 + t * w0, 0.0), max_act)
    l0_b1 = tl.minimum(tl.maximum(u * b1 + t * w1, 0.0), max_act)

    out = l0_ptr + pid_b * L1 + cols
    tl.store(out, l0_w0 * l0_w1, mask=cmask)
    tl.store(out + HALF, l0_b0 * l0_b1, mask=cmask)
    cl = cl_ptr + pid_b * (4 * HALF) + cols
    tl.store(cl, l0_w0, mask=cmask)
    tl.store(cl + HALF, l0_w1, mask=cmask)
    tl.store(cl + 2 * HALF, l0_b0, mask=cmask)
    tl.store(cl + 3 * HALF, l0_b1, mask=cmask)


@triton.jit
def _fused_bwd_kernel(
    us_ptr,
    them_ptr,
    widx_ptr,
    bidx_ptr,
    gl0_ptr,
    cl_ptr,
    gw_ptr,
    gb_ptr,
    max_act,
    batch_size,
    A: tl.constexpr,
    L1: tl.constexpr,
    HALF: tl.constexpr,
    KC: tl.constexpr,
    BLOCK_C: tl.constexpr,
    POS: tl.constexpr,
):
    pid_p = tl.program_id(0)
    cols = tl.program_id(1) * BLOCK_C + tl.arange(0, BLOCK_C)
    cmask = cols < HALF
    gb0 = tl.zeros([BLOCK_C], dtype=tl.float32)
    gb1 = tl.zeros([BLOCK_C], dtype=tl.float32)
    for p in range(POS):
        b = pid_p * POS + p
        if b < batch_size:
            b64 = b.to(tl.int64)
            cl = cl_ptr + b64 * (4 * HALF) + cols
            cw0 = tl.load(cl, mask=cmask, other=0.0)
            cw1 = tl.load(cl + HALF, mask=cmask, other=0.0)
            cb0 = tl.load(cl + 2 * HALF, mask=cmask, other=0.0)
            cb1 = tl.load(cl + 3 * HALF, mask=cmask, other=0.0)
            gp = gl0_ptr + b64 * L1 + cols
            g_i = tl.load(gp, mask=cmask, other=0.0)
            g_ih = tl.load(gp + HALF, mask=cmask, other=0.0)

            dw0 = tl.where((cw0 == 0.0) | (cw0 == max_act), 0.0, g_i * cw1)
            dw1 = tl.where((cw1 == 0.0) | (cw1 == max_act), 0.0, g_i * cw0)
            db0 = tl.where((cb0 == 0.0) | (cb0 == max_act), 0.0, g_ih * cb1)
            db1 = tl.where((cb1 == 0.0) | (cb1 == max_act), 0.0, g_ih * cb0)

            u = tl.load(us_ptr + b64)
            t = tl.load(them_ptr + b64)
            g_w0 = u * dw0 + t * db0
            g_w1 = u * dw1 + t * db1
            g_b0 = t * dw0 + u * db0
            g_b1 = t * dw1 + u * db1
            gb0 += g_w0 + g_b0
            gb1 += g_w1 + g_b1

            nz_w0 = cmask & (g_w0 != 0.0)
            nz_w1 = cmask & (g_w1 != 0.0)
            nz_b0 = cmask & (g_b0 != 0.0)
            nz_b1 = cmask & (g_b1 != 0.0)
            for k0 in tl.static_range(0, A, KC):
                ks = k0 + tl.arange(0, KC)
                km = ks < A
                wi = tl.load(widx_ptr + b64 * A + ks, mask=km, other=-1)
                bi = tl.load(bidx_ptr + b64 * A + ks, mask=km, other=-1)
                wv = wi >= 0
                bv = bi >= 0
                pw = gw_ptr + (tl.where(wv, wi, 0).to(tl.int64) * L1)[:, None] + cols[None, :]
                pb = gw_ptr + (tl.where(bv, bi, 0).to(tl.int64) * L1)[:, None] + cols[None, :]
                tl.atomic_add(
                    pw,
                    tl.broadcast_to(g_w0[None, :], [KC, BLOCK_C]),
                    mask=wv[:, None] & nz_w0[None, :],
                    sem="relaxed",
                )
                tl.atomic_add(
                    pw + HALF,
                    tl.broadcast_to(g_w1[None, :], [KC, BLOCK_C]),
                    mask=wv[:, None] & nz_w1[None, :],
                    sem="relaxed",
                )
                tl.atomic_add(
                    pb,
                    tl.broadcast_to(g_b0[None, :], [KC, BLOCK_C]),
                    mask=bv[:, None] & nz_b0[None, :],
                    sem="relaxed",
                )
                tl.atomic_add(
                    pb + HALF,
                    tl.broadcast_to(g_b1[None, :], [KC, BLOCK_C]),
                    mask=bv[:, None] & nz_b1[None, :],
                    sem="relaxed",
                )
    tl.atomic_add(gb_ptr + cols, gb0, mask=cmask & (gb0 != 0.0), sem="relaxed")
    tl.atomic_add(gb_ptr + HALF + cols, gb1, mask=cmask & (gb1 != 0.0), sem="relaxed")


def _pow2_at_most(n: int, cap: int) -> int:
    p = 1
    while p * 2 <= min(n, cap):
        p *= 2
    return p


def _block_cols(width: int) -> int:
    # Columns per program; env override for tuning runs.
    return _env_int("NNUE_TRITON_BLOCK_C", _pow2_at_most(width, 128))


def _k_chunk(active: int) -> int:
    return _env_int("NNUE_TRITON_KC", min(16, triton.next_power_of_2(active)))


def _num_warps() -> int:
    return _env_int("NNUE_TRITON_WARPS", 4)


def _pos_per_program() -> int:
    return _env_int("NNUE_TRITON_POS", 8)


@torch.compiler.disable
def sparse_linear_forward(indices, weight, bias):
    batch_size, active = indices.shape
    n = weight.shape[1]
    out = torch.empty(batch_size, n, dtype=torch.float32, device=weight.device)
    if batch_size == 0:
        return out
    bn = _block_cols(n)
    grid = (batch_size, triton.cdiv(n, bn))
    _sparse_fwd_kernel[grid](
        indices,
        weight,
        bias,
        out,
        A=active,
        N=n,
        KC=_k_chunk(active),
        BLOCK_N=bn,
        num_warps=_num_warps(),
    )
    return out


@torch.compiler.disable
def sparse_linear_backward(indices, grad_output, num_inputs):
    batch_size, active = indices.shape
    n = grad_output.shape[1]
    device = grad_output.device
    grad_weight = torch.zeros(num_inputs, n, dtype=torch.float32, device=device)
    grad_bias = torch.zeros(n, dtype=torch.float32, device=device)
    if batch_size == 0:
        return grad_weight, grad_bias
    bn = _block_cols(n)
    pos = _pos_per_program()
    grid = (triton.cdiv(batch_size, pos), triton.cdiv(n, bn))
    _sparse_bwd_kernel[grid](
        indices,
        grad_output,
        grad_weight,
        grad_bias,
        batch_size,
        A=active,
        N=n,
        KC=_k_chunk(active),
        BLOCK_N=bn,
        POS=pos,
        num_warps=_num_warps(),
    )
    return grad_weight, grad_bias


@torch.compiler.disable
def fused_double_ft_forward(
    us, them, white_indices, black_indices, weight, bias, max_ft_activation, l1_size
):
    batch_size, active = white_indices.shape
    half = l1_size // 2
    device = weight.device
    l0 = torch.empty(batch_size, l1_size, dtype=torch.float32, device=device)
    clamped = torch.empty(batch_size, 4, half, dtype=torch.float32, device=device)
    if batch_size == 0:
        return l0, clamped
    bc = _block_cols(half)
    grid = (batch_size, triton.cdiv(half, bc))
    _fused_fwd_kernel[grid](
        us,
        them,
        white_indices,
        black_indices,
        weight,
        bias,
        l0,
        clamped,
        float(max_ft_activation),
        A=active,
        L1=l1_size,
        HALF=half,
        KC=_k_chunk(active),
        BLOCK_C=bc,
        num_warps=_num_warps(),
    )
    return l0, clamped


@torch.compiler.disable
def fused_double_ft_backward(
    us,
    them,
    white_indices,
    black_indices,
    grad_l0,
    clamped,
    num_inputs,
    max_ft_activation,
    l1_size,
):
    batch_size, active = white_indices.shape
    half = l1_size // 2
    device = grad_l0.device
    grad_weight = torch.zeros(num_inputs, l1_size, dtype=torch.float32, device=device)
    grad_bias = torch.zeros(l1_size, dtype=torch.float32, device=device)
    if batch_size == 0:
        return grad_weight, grad_bias
    bc = _block_cols(half)
    pos = _pos_per_program()
    grid = (triton.cdiv(batch_size, pos), triton.cdiv(half, bc))
    _fused_bwd_kernel[grid](
        us,
        them,
        white_indices,
        black_indices,
        grad_l0,
        clamped,
        grad_weight,
        grad_bias,
        float(max_ft_activation),
        batch_size,
        A=active,
        L1=l1_size,
        HALF=half,
        KC=_k_chunk(active),
        BLOCK_C=bc,
        POS=pos,
        num_warps=_num_warps(),
    )
    return grad_weight, grad_bias
