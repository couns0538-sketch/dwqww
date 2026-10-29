# nnue-pytorch AMD port (R6) - GPL-3.0

Everything in this folder is part of, or derived from, **nnue-pytorch** (official-stockfish/nnue-pytorch, pinned
b2614500) and is licensed **GPL-3.0** (see `LICENSE`, copied from nnue-pytorch). It is a tool for the trainer only.
**Nothing here may be copied into the Forge engine sources** (`IDEA_SOURCE.md`). Report: `docs/OPUS_R6_AMD_NNUE.md`.

## What it is
Triton kernels that replace nnue-pytorch's CuPy/CUDA kernels on AMD GPUs. ROCm on Windows has no CuPy.

| upstream CuPy kernel | Triton replacement | used by |
|---|---|---|
| `fused_ft_kernel.py` (fused double FT fwd + scatter bwd) | `triton_ft_kernels.py` `_fused_fwd_kernel`, `_fused_bwd_kernel` | `double_feature_transform`, backend `auto` / `triton` |
| `sparse_linear_kernel.py` | `_sparse_fwd_kernel`, `_sparse_bwd_kernel` | `SparseLinearFunction`, backend `auto` / `triton-sparse` |
| `ranger_lite.py` fused update (5 kernels) | `ranger_lite_triton.py` | `RangerLite.step` when CuPy is missing |

Plus Windows fixes: the end-of-run crash (`train.py`), loader CMake (BMI2 on Windows, MSVC-style flags), and
`NNUE_DATA_LOADER_LIB`.

## Layout
- `patches/0001..0004-*.patch`: `git am` onto b2614500.
- `src/`: the changed files at their repo paths.
  - New: `model/modules/feature_transformer/triton_ft_kernels.py`, `triton_ft_functions.py`,
    `model/optimizers/ranger_lite_triton.py`, `tests/test_amd_triton_ft.py`, `tests/test_amd_triton_ranger.py`,
    `tests/bench_amd_triton_ft.py`.
  - Patched: `double_ft_functions.py`, `sparse_linear_functions.py`, `ranger_lite.py`, `train.py`,
    `data_loader/_native.py`, `data_loader/cpp/CMakeLists.txt`.
- `env.sh`: the environment for every run (venv `Scripts` on PATH, thread caps, TMP and caches on scratch).
- `guard/guard_exec.py`: RAM watchdog runner. It aborts its own job below `R6_MIN_FREE_GB` (default 7);
  `R6_EPOCH_TIMER=1` + `R6_EPOCH_SIZE` print pos/s per epoch for train.py.
- `bench/`: `final_bench.sh` (the final smoke-size A/B set), `bench_train.py` (older runner, no in-run guard),
  `profile_train.py` (per-phase step times).
- `debug/`: NaN hunters (`nan_hunt*.py`), `denormal_probe.py`, `planted_sqrt_bug.py`.
- `loader/`: `build_loader.sh`, `bench_loader.sh`, `dl_equal.py`, `LOADER_NOTES.md`.
- `logs/`: every number in the report, plus the incident evidence.

## Use
```
source tools/nnue_pytorch_amd/env.sh          # or activate F:\nnue_pytorch\venv - REQUIRED for Triton
cd <nnue-pytorch checkout with the patches>
python ../guard/guard_exec.py tests/test_amd_triton_ft.py --small
python ../guard/guard_exec.py tests/test_amd_triton_ranger.py
TORCHINDUCTOR_COMPILE_THREADS=1 python ../guard/guard_exec.py train.py <usual args>
```
Flags:
- `NNUE_FT_BACKEND=auto|triton|triton-sparse|torch|fused|sparse`. `torch` is the plain PyTorch fallback.
- `NNUE_RANGER_FUSED=0` gives the Python optimizer path.
- `NNUE_DATA_LOADER_LIB=<dll>`.
- `TORCHDYNAMO_DISABLE=1` turns off compile.

## PC rules (grok-pc, after the 2026-10-29 incident)
- Run everything through `guard_exec.py` (aborts below 7 GB free RAM).
- While the live Forge trainer runs, only smoke-size runs: batch <= 4096, L1 <= 256, 1 loader worker.
- Never touch `F:\forge_nnue_train`.
