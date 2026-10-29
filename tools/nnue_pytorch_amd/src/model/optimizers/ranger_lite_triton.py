"""Triton versions of the fused RangerLite update kernels (GPL-3.0, nnue-pytorch).

Same arithmetic as the CuPy kernels in ranger_lite.py (_RangerLiteFusedKernels),
one element per lane, so AMD GPUs (ROCm on Windows, no CuPy) get the fused path.
All tensors are contiguous fp32 on one GPU; scalars are passed as fp32.

Denormals: on gfx1100 with triton-windows 3.6, tl.sqrt_rn returns NaN for
every fp32 denormal input (tl.sqrt flushes them to 0). variance_ma reaches
denormals once a gradient is ~1e-19, so the denominator flushes them to 0
first; the result differs from the exact sqrt by < 1e-19 before eps (1e-7).
"""

import torch
import triton
import triton.language as tl

BLOCK = 1024
_FLT_MIN = tl.constexpr(1.1754943508222875e-38)  # smallest normal fp32


@triton.jit
def _sqrt_no_denormal(x):
    return tl.sqrt_rn(tl.where(x < _FLT_MIN, 0.0, x))


@triton.jit
def _pnm_full_kernel(
    p_ptr, g_ptr, gm_ptr, ngm_ptr, vm_ptr, n,
    beta2, one_minus_beta2, bias_correction2, beta1_sq, one_minus_beta1_sq,
    one_plus_pnm, pnm_factor, noise_norm, lr_div_bc1, eps, wd_factor,
    ODD: tl.constexpr, BLOCK: tl.constexpr,
):
    offs = tl.program_id(0).to(tl.int64) * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    g = tl.load(g_ptr + offs, mask=m, other=0.0)
    vm = tl.load(vm_ptr + offs, mask=m, other=0.0) * beta2 + g * g * one_minus_beta2
    tl.store(vm_ptr + offs, vm, mask=m)
    denom = _sqrt_no_denormal(vm / bias_correction2) + eps
    gm = tl.load(gm_ptr + offs, mask=m, other=0.0)
    ngm = tl.load(ngm_ptr + offs, mask=m, other=0.0)
    if ODD:
        pgm = gm
        pngm = ngm
    else:
        pgm = ngm
        pngm = gm
    new_pgm = pgm * beta1_sq + g * one_minus_beta1_sq
    pnm_val = (new_pgm * one_plus_pnm - pngm * pnm_factor) / noise_norm
    p = tl.load(p_ptr + offs, mask=m, other=0.0)
    p = p * (1.0 - wd_factor)
    p = p - lr_div_bc1 * (pnm_val / denom)
    tl.store(p_ptr + offs, p, mask=m)
    if ODD:
        tl.store(gm_ptr + offs, new_pgm, mask=m)
    else:
        tl.store(ngm_ptr + offs, new_pgm, mask=m)


@triton.jit
def _adam_full_kernel(
    p_ptr, g_ptr, gm_ptr, vm_ptr, n,
    beta2, one_minus_beta2, bias_correction2, beta1, one_minus_beta1,
    lr_div_bc1, eps, wd_factor,
    BLOCK: tl.constexpr,
):
    offs = tl.program_id(0).to(tl.int64) * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    g = tl.load(g_ptr + offs, mask=m, other=0.0)
    vm = tl.load(vm_ptr + offs, mask=m, other=0.0) * beta2 + g * g * one_minus_beta2
    tl.store(vm_ptr + offs, vm, mask=m)
    denom = _sqrt_no_denormal(vm / bias_correction2) + eps
    gm = tl.load(gm_ptr + offs, mask=m, other=0.0) * beta1 + g * one_minus_beta1
    tl.store(gm_ptr + offs, gm, mask=m)
    p = tl.load(p_ptr + offs, mask=m, other=0.0)
    p = p * (1.0 - wd_factor)
    p = p - lr_div_bc1 * (gm / denom)
    tl.store(p_ptr + offs, p, mask=m)


@triton.jit
def _variance_kernel(g_ptr, vm_ptr, n, beta2, one_minus_beta2, BLOCK: tl.constexpr):
    offs = tl.program_id(0).to(tl.int64) * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    g = tl.load(g_ptr + offs, mask=m, other=0.0)
    vm = tl.load(vm_ptr + offs, mask=m, other=0.0) * beta2 + g * g * one_minus_beta2
    tl.store(vm_ptr + offs, vm, mask=m)


@triton.jit
def _pnm_phase2_kernel(
    p_ptr, g_ptr, gm_ptr, ngm_ptr, vm_ptr, n,
    bias_correction2, beta1_sq, one_minus_beta1_sq,
    one_plus_pnm, pnm_factor, noise_norm, lr_div_bc1, eps, wd_factor,
    ODD: tl.constexpr, BLOCK: tl.constexpr,
):
    offs = tl.program_id(0).to(tl.int64) * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    vm = tl.load(vm_ptr + offs, mask=m, other=0.0)
    denom = _sqrt_no_denormal(vm / bias_correction2) + eps
    g = tl.load(g_ptr + offs, mask=m, other=0.0)
    gm = tl.load(gm_ptr + offs, mask=m, other=0.0)
    ngm = tl.load(ngm_ptr + offs, mask=m, other=0.0)
    if ODD:
        pgm = gm
        pngm = ngm
    else:
        pgm = ngm
        pngm = gm
    new_pgm = pgm * beta1_sq + g * one_minus_beta1_sq
    pnm_val = (new_pgm * one_plus_pnm - pngm * pnm_factor) / noise_norm
    p = tl.load(p_ptr + offs, mask=m, other=0.0)
    p = p * (1.0 - wd_factor)
    p = p - lr_div_bc1 * (pnm_val / denom)
    tl.store(p_ptr + offs, p, mask=m)
    if ODD:
        tl.store(gm_ptr + offs, new_pgm, mask=m)
    else:
        tl.store(ngm_ptr + offs, new_pgm, mask=m)


@triton.jit
def _adam_phase2_kernel(
    p_ptr, g_ptr, gm_ptr, vm_ptr, n,
    bias_correction2, beta1, one_minus_beta1, lr_div_bc1, eps, wd_factor,
    BLOCK: tl.constexpr,
):
    offs = tl.program_id(0).to(tl.int64) * BLOCK + tl.arange(0, BLOCK)
    m = offs < n
    vm = tl.load(vm_ptr + offs, mask=m, other=0.0)
    denom = _sqrt_no_denormal(vm / bias_correction2) + eps
    g = tl.load(g_ptr + offs, mask=m, other=0.0)
    gm = tl.load(gm_ptr + offs, mask=m, other=0.0) * beta1 + g * one_minus_beta1
    tl.store(gm_ptr + offs, gm, mask=m)
    p = tl.load(p_ptr + offs, mask=m, other=0.0)
    p = p * (1.0 - wd_factor)
    p = p - lr_div_bc1 * (gm / denom)
    tl.store(p_ptr + offs, p, mask=m)


def _grid(n):
    return (triton.cdiv(n, BLOCK),)


@torch.compiler.disable
def pnm_full(p, g, gm, ngm, vm, beta2, one_minus_beta2, bias_correction2, beta1_sq,
             one_minus_beta1_sq, one_plus_pnm, pnm_factor, noise_norm, lr_div_bc1, eps, step, wd_factor):
    n = p.numel()
    _pnm_full_kernel[_grid(n)](
        p, g, gm, ngm, vm, n,
        float(beta2), float(one_minus_beta2), float(bias_correction2), float(beta1_sq),
        float(one_minus_beta1_sq), float(one_plus_pnm), float(pnm_factor), float(noise_norm),
        float(lr_div_bc1), float(eps), float(wd_factor),
        ODD=bool(step & 1), BLOCK=BLOCK,
    )


@torch.compiler.disable
def adam_full(p, g, gm, vm, beta2, one_minus_beta2, bias_correction2, beta1, one_minus_beta1,
              lr_div_bc1, eps, wd_factor):
    n = p.numel()
    _adam_full_kernel[_grid(n)](
        p, g, gm, vm, n,
        float(beta2), float(one_minus_beta2), float(bias_correction2), float(beta1),
        float(one_minus_beta1), float(lr_div_bc1), float(eps), float(wd_factor),
        BLOCK=BLOCK,
    )


@torch.compiler.disable
def variance(g, vm, beta2, one_minus_beta2):
    n = g.numel()
    _variance_kernel[_grid(n)](g, vm, n, float(beta2), float(one_minus_beta2), BLOCK=BLOCK)


@torch.compiler.disable
def pnm_phase2(p, g, gm, ngm, vm, bias_correction2, beta1_sq, one_minus_beta1_sq, one_plus_pnm,
               pnm_factor, noise_norm, lr_div_bc1, eps, step, wd_factor):
    n = p.numel()
    _pnm_phase2_kernel[_grid(n)](
        p, g, gm, ngm, vm, n,
        float(bias_correction2), float(beta1_sq), float(one_minus_beta1_sq), float(one_plus_pnm),
        float(pnm_factor), float(noise_norm), float(lr_div_bc1), float(eps), float(wd_factor),
        ODD=bool(step & 1), BLOCK=BLOCK,
    )


@torch.compiler.disable
def adam_phase2(p, g, gm, vm, bias_correction2, beta1, one_minus_beta1, lr_div_bc1, eps, wd_factor):
    n = p.numel()
    _adam_phase2_kernel[_grid(n)](
        p, g, gm, vm, n,
        float(bias_correction2), float(beta1), float(one_minus_beta1), float(lr_div_bc1),
        float(eps), float(wd_factor),
        BLOCK=BLOCK,
    )
