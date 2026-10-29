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

## J3: speed (interim, 13:45 PC clock; GPU shared with the live DirectML trainer)
### FT layer alone (`tests/bench_amd_triton_ft.py`, synthetic batches, 75% of slots active, median of 10)
| shape | torch fwd | torch fwd+bwd | Triton fwd | Triton fwd+bwd | speedup fwd / fwd+bwd |
|---|---|---|---|---|---|
| B 4096, 32 active, 73728 inputs, L1 256 (baseline config) | 1.65 ms | 7.12 ms | 0.32 ms | 1.54 ms | 5.1x / 4.6x |
| B 16384, 32 active, 73728 inputs, L1 1024 | 21.35 ms | 58.45 ms | 8.08 ms | 26.46 ms | 2.6x / 2.2x |
| B 4096, 288 active, 138096 inputs, L1 1024 (full upstream features) | 37.70 ms | 104.22 ms | 23.99 ms | 56.72 ms | 1.6x / 1.8x |

### Short training runs (`bench/bench_train.py`; positions/s per epoch from epoch-end timestamps, median of epochs 2..N)
Same command as the 210k/s baseline: `train.py .pgo/small.binpack --features K32H3^ --l1 256 --accelerator cuda
--batch-size 4096 --epoch-size 204800`, here `--max-epochs 8|10 --threads 2 --num-workers 1`, BelowNormal.

| run | FT backend | torch.compile | median pos/s | per-epoch range |
|---|---|---|---|---|
| base_torch_l256 | torch | off (`TORCHDYNAMO_DISABLE=1`, as the baseline) | 165,044 | 143k-205k |
| torch_compile_l256 | torch | on (inductor, 1 compile thread) | 239,377 | 234k-247k |
| tri_l256 | Triton | off | 263,796 | 182k-269k |
| tri_compile_l256 | Triton | on | **335,637** | 321k-341k |

vs the 210k/s reference of SETUP_REPORT: 1.6x; vs the same-session torch run: 2.0x. torch.compile works now
because Triton works (it failed before with `TritonMissing` / the `hip_utils.c` build error).

Step breakdown, Triton FT without compile (`bench/profile_train.py`, synced timers, 240 steps, 21.7 ms/step with
the sync cost): forward+loss 6.6 ms, backward 5.4 ms, **RangerLite step 5.25 ms** (CuPy-only fused kernel missing ->
Python path), loader/H2D/Python 4.4 ms. Next: Triton port of the fused RangerLite kernels.

## Next
RangerLite Triton kernels + test, re-run J3, then J4 (loader, end-of-run crash).
