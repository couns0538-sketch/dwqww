# OPUS R6 - nnue-pytorch on AMD (RX 7900 XT, gfx1100, Windows ROCm)

Status: **WIP**, updated 14:25 PC clock (job start 13:24). J1 (FT + RangerLite kernels), J2, J3 (smoke config)
and J4 (crash fix, loader builds) are done. Still open: grouped-L1 kernel, J3 at the full feature set, final
review. Everything was measured on a PC that was busy the whole time (a live DirectML trainer on the same GPU,
gates and self-play on the CPU). Speed numbers are same-session A/B comparisons, not clean absolute numbers.
No Elo claims.

## Where things are
- Port (GPL-3.0, from nnue-pytorch b2614500): `tools/nnue_pytorch_amd/` in this branch. It has `patches/`
  (3 `git format-patch` files against b2614500), `src/` (the changed files at their repo paths), tests,
  bench/debug/loader tools and logs.
- Working clone: `F:\opus_scratch\r6\nnue-pytorch-amd`, branch `opus-r6-amd`, 3 commits on top of b2614500.
  `F:\nnue_pytorch\repo` is **not modified**. Grok Bot works there in parallel.
- Venv: `F:\nnue_pytorch\venv`, used read-only. It has torch 2.11.0+rocm7.13.0, triton-windows 3.6.0.post26,
  and rocm-sdk-devel 7.13.0 (the last two installed by Grok Bot at 13:25 / 13:28).
- Environment: `tools/nnue_pytorch_amd/env.sh`. It puts the venv `Scripts` folder on PATH, which Triton needs;
  it also sets the thread caps, TMP and the Triton/inductor caches under `F:\opus_scratch\r6`.

## Flags (the plain PyTorch fallback stays available)
| env var | values | default |
|---|---|---|
| `NNUE_FT_BACKEND` | `auto`, `triton`, `triton-sparse`, `torch`, `fused`, `sparse` | `auto`: CuPy if present (upstream unchanged), else Triton if a probe kernel passes, else `torch` |
| `NNUE_RANGER_FUSED` | `1`, `0` | `1`: without CuPy, use the Triton fused RangerLite kernels; `0` = Python update path |
| `NNUE_DATA_LOADER_LIB` | path to a loader DLL | unset = upstream glob (newest file wins) |
| `NNUE_TRITON_BLOCK_C`, `_KC`, `_WARPS`, `_POS` | tuning knobs | 128 / 16 / 4 / 8 |

## J1: kernels ported
| upstream CuPy kernel (CUDA) | Triton replacement | status |
|---|---|---|
| `fused_ft_kernel.py` (fused double-perspective FT forward + scatter backward) | `triton_ft_kernels.py` `_fused_fwd_kernel`, `_fused_bwd_kernel` | done, J2 PASS |
| `sparse_linear_kernel.py` (sparse linear forward/backward) | `_sparse_fwd_kernel`, `_sparse_bwd_kernel` | done, J2 PASS |
| `ranger_lite.py` `_RangerLiteFusedKernels` (5 kernels) | `ranger_lite_triton.py` | done, test PASS (incl. denormal case) |
| `aggregated_ft_kernel.py` | none needed: NVIDIA-only upstream (`torch.version.hip` disables it) | n/a |
| `grouped_linear.py` (grouped L1 for 32 layer stacks) | not ported yet: NVIDIA-only upstream; dense path used | open |

Also unlocked: **torch.compile (inductor) works now**. It failed before only because Triton was missing.

### Triton on this PC: what made it work, and what fails
- Works once the venv `Scripts` folder is on PATH. Triton's AMD driver finds the HIP headers through
  `rocm-sdk path --root`. Without it, it fails exactly as in Grok Bot's smoke test:
  `hip_utils.c(2,10): fatal error: 'hip/hip_runtime.h' file not found`
  (`tools/nnue_pytorch_amd/logs/triton_without_venv_on_PATH.log`).
- **Bug found: `tl.sqrt_rn` returns NaN for every fp32 denormal input on gfx1100** (triton-windows 3.6;
  `tl.sqrt` flushes to 0, torch is exact). Probe output: `logs/denormal_probe.log`.
  The first RangerLite port therefore went NaN in real training, while its unit test (gradients ~1e-2) passed.
  - How it was found: a shadow check ran the real fused step and the Python step on cloned state each step
    (`debug/nan_hunt4.py`). At step 112 one element of the output layer was NaN (fused) vs 0.063 (Python), with
    grad 5.9e-19, which puts `variance_ma` ~ g^2 * 1e-3 in the denormal range.
  - Fix: flush denormals before `sqrt_rn`.
  - The test now has a denormal-gradient case. A planted-bug run (old kernel) fails all 6 denormal cases and the
    fixed kernel passes them (`logs/j1_ranger_planted.log`, `logs/j1_ranger_test_run3.log`).
  - Wrong turns, recorded so nobody repeats them: a stream race was suspected first. "Serialized HIP: no NaN"
    and "host-side event wait: no NaN" were luck, because batch order varies between runs; the compiled run with
    kernel serialization still went NaN.

## J2: correctness (PASS)
`src/tests/test_amd_triton_ft.py`: random sparse batches with unique indices per row, -1 padding, us/them 0/1,
weights 0.3*randn so the clamp hits both 0 and max, grad_out = randn/batch. Max abs diff vs backend `torch`:

| case (batch, active, inputs, L1) | path | fwd | grad_w | grad_b |
|---|---|---|---|---|
| tiny-odd (7, 5, 50, 96) | double / sparse | 6.0e-08 / 1.2e-07 | 1.5e-08 / 0 | 3.0e-08 / 6.0e-08 |
| holes (33, 12, 300, 128; -1 mid-row) | double / sparse | 2.4e-07 / 3.6e-07 | 1.1e-08 / 1.5e-08 | 2.2e-08 / 6.0e-08 |
| k32h3-l256 (4096, 32, 73728, 256) | double / sparse | 9.8e-07 / 1.9e-06 | 4.7e-10 / 2.3e-10 | 1.0e-08 / 2.7e-08 |
| k32h3-l1024 (1024, 32, 73728, 1024) | double / sparse | 9.8e-07 / 1.9e-06 | 1.9e-09 / 9.3e-10 | 2.2e-08 / 3.0e-08 |
| collide (2048, 32, 64, 256) | double / sparse | 7.7e-07 / 1.9e-06 | 1.5e-08 / 4.5e-08 | 9.3e-09 / 3.0e-08 |
| full288-l1024 (256, 288, 138096, 1024) | double / sparse | 7.2e-06 / 1.2e-05 | 2.7e-08 / 3.7e-09 | 3.2e-08 / 4.5e-08 |

Stress case (grad_out = randn; relative error vs a float64 run): torch fp32 7.9e-07 / 1.1e-07 / 1.3e-07,
Triton 5.6e-07 / 2.1e-07 / 6.4e-07 -> PASS. RangerLite (`src/tests/test_amd_triton_ranger.py`): fused vs Python
path over 12 steps, 4 params incl. 73728x256. It covers paths A, B and A+wd, pnm on/off, normal and denormal
gradients. Max abs diff <= 3.6e-07, and kernel-call counts prove which path ran -> PASS.

## J3: speed
### FT layer alone (`src/tests/bench_amd_triton_ft.py`, synthetic, 75% of slots active, median of 10)
| shape | torch fwd / fwd+bwd | Triton fwd / fwd+bwd | speedup |
|---|---|---|---|
| B 4096, 32 active, 73728 inputs, L1 256 (smoke config) | 1.65 / 7.12 ms | 0.32 / 1.54 ms | 5.1x / 4.6x |
| B 16384, 32 active, 73728 inputs, L1 1024 | 21.35 / 58.45 ms | 8.08 / 26.46 ms | 2.6x / 2.2x |
| B 4096, 288 active, 138096 inputs, L1 1024 (full upstream features) | 37.70 / 104.22 ms | 23.99 / 56.72 ms | 1.6x / 1.8x |

### Short training runs (`bench/bench_train.py`; pos/s per epoch from epoch-end timestamps; median of epochs 2..N)
Same command as the 210k/s baseline: `train.py .pgo/small.binpack --features K32H3^ --l1 256 --accelerator cuda
--batch-size 4096 --epoch-size 204800`, here with `--max-epochs 8|10 --threads 2 --num-workers 1`, BelowNormal.

| run | FT | optimizer | torch.compile | median pos/s | NaN |
|---|---|---|---|---|---|
| base_torch_l256 | torch | Python | off (as the baseline) | 165,044 | no |
| torch_compile_l256 | torch | Python | on | 239,377 | no |
| tri_l256 | Triton | Python | off | 263,796 | no |
| tri_compile_l256 | Triton | Python | on | 335,637 | no |
| triRfix_eager | Triton | Triton (fixed) | off | 318,463 | no |
| **triRfix_compile** | Triton | Triton (fixed) | on | **435,621** | no |
| crashfix_check (4 epochs, after the J4 fix) | Triton | Triton | on | 430,933, exit 0 | no |

**Result: 436k pos/s vs the 210k/s reference = 2.1x, and vs the same-session torch run (165k) = 2.6x.**
Before the fix, runs with the unfixed Triton optimizer (triR_*) went NaN; those are kept in `logs/bench/` as
evidence. Step breakdown before the RangerLite port (Triton FT, synced timers, 21.7 ms/step): fwd+loss 6.6,
backward 5.4, RangerLite 5.25 (Python path), loader/H2D/Python 4.4.

## J4: Windows data loader and end-of-run crash
- **Crash fixed.** `train.py:452 dist.is_initialized()` -> `dist.is_available() and dist.is_initialized()`, the
  same guard the rest of the code base uses. A run now exits 0 and writes `training_finished` + `last.ckpt`.
  `serialize.py` exports the checkpoint (17.6 MB .nnue, `logs/j4_serialize.log`).
- **Loader builds** (`loader/build_loader.sh`; CMake patch: `NNUE_BMI2=AUTO|ON|OFF`, and AUTO on Windows now
  asks the compiler for fast BMI2; MSVC-style flags for cl/clang-cl). Single-thread loader bench,
  `Full_Threats+PP_3Wide+K32H3`, small.binpack, 40 x 131072 positions, alternating, 2 rounds:

| build | MPos/s (round 1 / 2) | vs setup |
|---|---|---|
| setup: MSYS2 g++ 15.2, -static, no BMI2 | 0.249 / 0.249 | 1.00x |
| g++ + BMI2 (auto-detected on Windows now) | 0.264 / 0.264 | 1.06x |
| g++ + BMI2 + PGO (needed `-Wl,--exclude-libs,ALL`) | 0.269 / 0.272 | 1.08x |
| **AMD clang 23 (ROCm SDK), MSVC ABI, static CRT, BMI2** | **0.460 / 0.473** | **1.88x** |

  - LLVM 18 (`C:\Program Files\LLVM`) cannot build against the MSVC 14.51 STL:
    `error STL1000: Unexpected compiler version, expected Clang 20 or newer`. The ROCm SDK's clang 23 can.
  - Equality (`loader/dl_equal.py`):
    - Features from a fixed list of 32,768 FENs are bit-identical across all builds (K32H3 and the full set).
    - The binpack stream is bit-identical between the g++ builds. With clang/MSVC the first shuffle window
      (1,048,576 positions) holds the **same multiset of positions** in a different order: `std::shuffle` is
      implementation-defined (libstdc++ vs MSVC STL), so later windows differ, and they are equally valid.
  - Training effect at the smoke config: none (setup vs clang DLL, 1 or 2 workers: 424k-436k). The GPU step is
    the bottleneck there; the loader matters for bigger feature sets or more workers.

## Open items / next
- grouped-L1 Triton kernel (only pays off at L1 1024 and above).
- J3 at the full upstream feature set.
- Final review pass.
