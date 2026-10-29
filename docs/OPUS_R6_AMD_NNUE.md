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

## J1 status: Triton kernels written and wired in (13:37 PC clock)
- Triton works on the RX 7900 XT under Windows ROCm once `rocm-sdk` (venv `Scripts`) is on `PATH`:
  `tools/nnue_pytorch_amd/triton_smoke_r6.py` -> add, fp32 `atomic_add`, 2-D gather all OK
  (`tools/nnue_pytorch_amd/logs/triton_smoke_r6.log`). Grok Bot's earlier failure: Triton's AMD driver could not
  compile its `hip_utils.c` because `rocm-sdk path --root` was not found, so no HIP include dir was passed to
  `clang-cl` (its log shows only `triton\backends\amd\include`, which does not exist).
- New: `triton_ft_kernels.py` (fused double FT fwd/bwd, sparse linear fwd/bwd), `triton_ft_functions.py`
  (autograd + one-time probe), backend choice in `double_ft_functions.py` / `sparse_linear_functions.py`.
- Flag: `NNUE_FT_BACKEND=auto|triton|triton-sparse|torch|fused|sparse`; `torch` = plain PyTorch fallback;
  `auto` = CuPy if present (upstream behaviour unchanged), else Triton if the probe passes, else torch.

## J2: correctness (PASS, 13:36 PC clock)
`tests/test_amd_triton_ft.py`, random sparse batches, unique indices per row, -1 padding, us/them 0/1,
weights 0.3*randn (clamp at 0 and at max_act=1.0 both hit), grad_out = randn/batch. Max abs diff vs backend
`torch`:

| case (batch, active, inputs, L1) | path | fwd | grad_w | grad_b |
|---|---|---|---|---|
| tiny-odd (7, 5, 50, 96) | double | 6.0e-08 | 1.5e-08 | 3.0e-08 |
| tiny-odd | sparse | 1.2e-07 | 0 | 6.0e-08 |
| holes (33, 12, 300, 128; -1 mid-row) | double | 2.4e-07 | 1.1e-08 | 2.2e-08 |
| holes | sparse | 3.6e-07 | 1.5e-08 | 6.0e-08 |
| k32h3-l256 (4096, 32, 73728, 256) | double | 9.8e-07 | 4.7e-10 | 1.0e-08 |
| k32h3-l256 | sparse | 1.9e-06 | 2.3e-10 | 2.7e-08 |
| k32h3-l1024 (1024, 32, 73728, 1024) | double | 9.8e-07 | 1.9e-09 | 2.2e-08 |
| k32h3-l1024 | sparse | 1.9e-06 | 9.3e-10 | 3.0e-08 |
| collide (2048, 32, 64, 256) | double | 7.7e-07 | 1.5e-08 | 9.3e-09 |
| collide | sparse | 1.9e-06 | 4.5e-08 | 3.0e-08 |
| full288-l1024 (256, 288, 138096, 1024) | double | 7.2e-06 | 2.7e-08 | 3.2e-08 |
| full288-l1024 | sparse | 1.2e-05 | 3.7e-09 | 4.5e-08 |

Stress (grad_out = randn, 4096 x 32 x 1000 x 256, relative error vs a float64 run): torch fp32
7.9e-07 / 1.1e-07 / 1.3e-07, Triton fp32 5.6e-07 / 2.1e-07 / 6.4e-07 (fwd / grad_w / grad_b) -> PASS (< 1e-5).
Log: `tools/nnue_pytorch_amd/logs/j2_test_run1.log`. Whole test: 31 s on the shared GPU.

## Next
J3 benchmark (short training runs, torch vs Triton, same settings as the 210k/s baseline), then J4.
