"""Autograd wrappers for the Triton feature-transformer kernels (GPL-3.0, nnue-pytorch).

Selected by double_ft_functions / sparse_linear_functions when CuPy is missing
(ROCm on Windows) or when NNUE_FT_BACKEND=triton / triton-sparse is set.
NNUE_FT_BACKEND=torch keeps the plain PyTorch path.
"""

import os
import sys

import torch
from torch import autograd

_HAS_TRITON_KERNELS = False
_TRITON_IMPORT_ERROR = None
try:
    from . import triton_ft_kernels as _tk

    _HAS_TRITON_KERNELS = True
except Exception as e:  # ImportError, or a broken Triton install
    _TRITON_IMPORT_ERROR = f"{type(e).__name__}: {e}"

_probe_cache: dict[str, bool] = {}


def requested_backend() -> str:
    return (os.environ.get("NNUE_FT_BACKEND", "auto").strip().lower()) or "auto"


@torch.compiler.disable
def triton_usable(device: torch.device) -> bool:
    """Compile and run a tiny kernel once per device; False (with a warning) on failure."""
    if not _HAS_TRITON_KERNELS:
        return False
    if device.type != "cuda":
        return False
    key = str(device)
    if key not in _probe_cache:
        try:
            idx = torch.tensor([[0, 2, -1, -1]], dtype=torch.int32, device=device)
            w = torch.arange(12, dtype=torch.float32, device=device).reshape(3, 4)
            b = torch.ones(4, dtype=torch.float32, device=device)
            out = _tk.sparse_linear_forward(idx, w, b)
            ref = w[0] + w[2] + b
            _probe_cache[key] = bool(torch.equal(out[0], ref))
            if not _probe_cache[key]:
                print("[nnue-amd] Triton probe gave a wrong result; using torch FT path", file=sys.stderr)
        except Exception as e:
            print(f"[nnue-amd] Triton probe failed ({type(e).__name__}: {e}); using torch FT path", file=sys.stderr)
            _probe_cache[key] = False
    return _probe_cache[key]


def triton_import_error() -> str | None:
    return _TRITON_IMPORT_ERROR


def _as_i32(t: torch.Tensor) -> torch.Tensor:
    if t.dtype != torch.int32:
        t = t.to(torch.int32)
    return t.contiguous()


class TritonSparseLinearFunction(autograd.Function):
    @staticmethod
    def forward(ctx, feature_indices, weight, bias):
        assert feature_indices.ndim == 2 and weight.ndim == 2 and bias.ndim == 1
        assert weight.dtype == torch.float32 and bias.dtype == torch.float32
        idx = _as_i32(feature_indices)
        ctx.save_for_backward(idx)
        ctx.num_inputs = weight.shape[0]
        return _tk.sparse_linear_forward(idx, weight.contiguous(), bias.contiguous())

    @staticmethod
    def backward(ctx, grad_output):
        (idx,) = ctx.saved_tensors
        grad_weight, grad_bias = _tk.sparse_linear_backward(
            idx, grad_output.contiguous(), ctx.num_inputs
        )
        return None, grad_weight, grad_bias


class TritonFusedDoubleFtFunction(autograd.Function):
    @staticmethod
    def forward(
        ctx,
        us,
        them,
        white_indices,
        black_indices,
        weight,
        bias,
        max_ft_activation,
        l1_size,
    ):
        assert l1_size % 2 == 0
        assert weight.ndim == 2 and bias.ndim == 1 and weight.shape[1] == bias.shape[0] == l1_size
        assert weight.dtype == torch.float32 and bias.dtype == torch.float32
        assert white_indices.shape == black_indices.shape
        us = us.contiguous().to(torch.float32)
        them = them.contiguous().to(torch.float32)
        assert us.numel() == them.numel() == white_indices.shape[0]
        wi = _as_i32(white_indices)
        bi = _as_i32(black_indices)
        l0, clamped = _tk.fused_double_ft_forward(
            us, them, wi, bi, weight.contiguous(), bias.contiguous(), max_ft_activation, l1_size
        )
        ctx.save_for_backward(us, them, wi, bi, clamped)
        ctx.max_ft_activation = float(max_ft_activation)
        ctx.l1_size = int(l1_size)
        ctx.num_inputs = weight.shape[0]
        return l0

    @staticmethod
    def backward(ctx, grad_l0):
        us, them, wi, bi, clamped = ctx.saved_tensors
        grad_weight, grad_bias = _tk.fused_double_ft_backward(
            us,
            them,
            wi,
            bi,
            grad_l0.contiguous(),
            clamped,
            ctx.num_inputs,
            ctx.max_ft_activation,
            ctx.l1_size,
        )
        return None, None, None, None, grad_weight, grad_bias, None, None
