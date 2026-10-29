# nnue-pytorch AMD port (R6) - GPL-3.0

Everything in this folder is part of / derived from **nnue-pytorch** (official-stockfish/nnue-pytorch,
pinned b2614500) and is licensed **GPL-3.0** (see `LICENSE`, copied from nnue-pytorch). It is a tool for the
trainer only. **Nothing here may be copied into the Forge engine sources** (see `IDEA_SOURCE.md`).

## What it is
Triton kernels that replace nnue-pytorch's CuPy/CUDA kernels on AMD GPUs (ROCm on Windows has no CuPy):

| upstream CuPy kernel | Triton replacement | used by |
|---|---|---|
| `fused_ft_kernel.py` fused double-perspective FT forward + scatter backward | `_fused_fwd_kernel`, `_fused_bwd_kernel` | `double_feature_transform` backend `auto` / `triton` |
| `sparse_linear_kernel.py` sparse linear forward/backward | `_sparse_fwd_kernel`, `_sparse_bwd_kernel` | `SparseLinearFunction` backend `auto` / `triton-sparse` |

Files (repo-relative paths inside nnue-pytorch, mirrored under `src/`):
- `model/modules/feature_transformer/triton_ft_kernels.py` (new): the four Triton kernels + launchers.
- `model/modules/feature_transformer/triton_ft_functions.py` (new): autograd wrappers, one-time probe.
- `model/modules/feature_transformer/double_ft_functions.py`, `sparse_linear_functions.py` (patched): backend choice.
- `tests/test_amd_triton_ft.py` (new): J2 correctness test.
- `patches/*.patch`: the same changes as `git format-patch` against b2614500.

## Flag (plain PyTorch fallback)
`NNUE_FT_BACKEND` = `auto` (default) | `triton` | `triton-sparse` | `torch` | `fused` | `sparse`.
- `auto`: CuPy fused kernel if CuPy exists (unchanged upstream behaviour), else Triton if a one-time probe kernel
  runs and gives the right answer, else the plain PyTorch path.
- `torch`: always the plain PyTorch (embedding_bag) path.

Tuning knobs (env, optional): `NNUE_TRITON_BLOCK_C` (columns per program, default min(128, pow2 <= half)),
`NNUE_TRITON_KC` (index chunk, default 16), `NNUE_TRITON_WARPS` (default 4), `NNUE_TRITON_POS` (positions per
backward program, default 8).

## Environment that makes Triton work on this PC
`triton-windows 3.6.0.post26` + `rocm-sdk-devel 7.13.0` in `F:\nnue_pytorch\venv` (both installed by Grok Bot on
2026-10-29 13:25 / 13:28). Triton's AMD driver finds the HIP headers through `rocm-sdk path --root`, so the venv's
`Scripts` folder must be on `PATH` (activate the venv, or `source env.sh`). With that, `triton_smoke_r6.py` passes:
add, fp32 `atomic_add`, 2-D gather (`logs/triton_smoke_r6.log`).

## Apply to a checkout of b2614500
```
cd F:\nnue_pytorch\repo        # or a clone
git am <this folder>\patches\0001-*.patch
```
or copy `src/` over the checkout.

## Results
See `docs/OPUS_R6_AMD_NNUE.md` in this branch (J2 table, J3 positions/s, J4 notes).
