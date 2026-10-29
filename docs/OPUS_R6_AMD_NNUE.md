# OPUS R6 - nnue-pytorch on AMD (RX 7900 XT, gfx1100, Windows ROCm)

Status: **WIP** (first push 2026-10-29 ~13:35 PC clock). This file is updated on every push.

## Scope
- J1 port the CuPy-only CUDA kernels of nnue-pytorch (pinned b2614500 at `F:\nnue_pytorch\repo`) to AMD:
  Triton (preferred) or HIP; plain PyTorch stays as fallback behind a flag.
- J2 correctness test vs the plain PyTorch path (max abs diff < 1e-4, forward and gradients).
- J3 positions/s on a short training run vs the 210k/s baseline from `F:\nnue_pytorch\SETUP_REPORT.md`.
- J4 (if time) Windows data loader speed, end-of-training crash.

## Licence boundary
nnue-pytorch is GPL-3.0. The port lives in `tools/nnue_pytorch_amd/` (GPL-3.0, own LICENSE note) and in the
scratch clone `F:\opus_scratch\r6\nnue-pytorch-amd` (branch `opus-r6-amd`). Nothing goes into Forge engine
sources; see `tools/nnue_pytorch_amd/IDEA_SOURCE.md`.

## Findings so far
- CuPy-only code on the ROCm path (b2614500):
  - `model/modules/feature_transformer/fused_ft_kernel.py`: fused double-perspective FT forward + scatter backward
    (the path `double_feature_transform(backend="auto")` takes when CuPy exists).
  - `model/modules/feature_transformer/sparse_linear_kernel.py`: single-perspective sparse linear fwd/bwd
    (`backend="sparse"`).
  - `model/modules/feature_transformer/aggregated_ft_kernel.py`: NVIDIA-only (disabled for HIP upstream).
  - `model/modules/grouped_linear.py`: grouped L1 for 32 layer stacks, NVIDIA-only (`torch.version.hip is None`).
  - `model/optimizers/ranger_lite.py`: fused RangerLite update (falls back to a Python update path).
- Another agent (Grok Bot) works in `F:\nnue_pytorch` at the same time: it installed `triton-windows 3.6.0.post26`
  at 13:25 and is installing `rocm[devel]==7.13.0` (rocm-sdk-devel, 3.4 GiB). Its Triton smoke failed while
  compiling Triton's `hip_utils.c` with the ROCm `clang-cl.exe`. I do not touch its files or the venv packages.
- The live trainer (`train_res*_v3b.py`, PID 12900) uses the same GPU through torch-directml; all GPU tests here
  are kept short.

## Next
Kernels, test script, benchmark (numbers will be added here).
