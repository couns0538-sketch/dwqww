# OPUS R6 - nnue-pytorch on AMD (RX 7900 XT, gfx1100, Windows ROCm)

Final report, 2026-10-29 (PC clock). No Elo claims. All speed numbers are same-session A/B runs on a busy PC: the
live DirectML trainer shares the GPU, and gates and self-play load the CPU.

## Summary
| job | result |
|---|---|
| J1 port CuPy kernels | **done** for everything that runs on ROCm: fused double FT fwd/bwd, sparse linear fwd/bwd, the fused RangerLite optimizer (5 kernels). Triton kernels, with the plain PyTorch path behind `NNUE_FT_BACKEND=torch` / `NNUE_RANGER_FUSED=0`. Not ported: grouped L1 (NVIDIA-only upstream, needs L1 >= 1024 to pay off, see "Not done"). The aggregated FT backward is NVIDIA-only upstream (`torch.version.hip` disables it) and is not needed. |
| J2 correctness | **PASS.** FT fwd/grad max abs diff <= 1.2e-5 (limit 1e-4) over 12 cases, plus a float64 stress check. RangerLite fused vs Python path <= 3.6e-7 over 12 cases (incl. denormal gradients), plus a fallback check and a planted-bug check. |
| J3 speed | Smoke config (the 210k baseline command): **448k-467k pos/s** with Triton FT + Triton RangerLite + torch.compile, against 196k-221k for the torch path in the same session (= the 210k reference). That is **2.1-2.2x**. Full feature set at the same small size: **35k -> 277k (8.0x)**. |
| J4 loader + crash | End-of-run crash fixed (exit 0, checkpoint + export OK). Loader: BMI2 on Windows (1.06x), g++ PGO (1.08x), AMD clang 23 MSVC-ABI build **1.88x per thread**. No training gain at smoke size (GPU-bound). Merge notes: `tools/nnue_pytorch_amd/loader/LOADER_NOTES.md`. |
| incident | **The live trainer crashed at 14:29:05 (out of memory) during my bigger J3 run.** Details below; the rules are tightened since. |

## INCIDENT, 14:29 PC clock: the live Forge trainer crashed, most likely because of my benchmark
- What happened: the live trainer `train_res*_v3b.py` (run `resid_h256_e48_f106_bs16k_lr10e4_b06_s406_fb8k`,
  PID 4616) died at **14:29:05** with `numpy.core._exceptions._ArrayMemoryError: Unable to allocate 2.12 MiB` in
  `pack_batch`. Its last log line (14:28:28) shows `sys_avail=6.28GB`; earlier lines showed 8.9 GB.
- Cause (most likely): my run `c2_triton` (K32H3^, L1 1024, batch 16384, 2 loader workers, inductor compile) used
  several GB more host RAM than the smoke runs. The RAM gate only checked >= 6 GB at the start, and the commit
  limit was reached.
- Aftermath:
  - From ~14:29, `import torch` (ROCm) and `hipInfo.exe` hung in new processes. No display-driver reset was
    logged. My next runs hung at start-up and were left alone (no-kill rule).
  - The owner restarted the trainer from `epoch013-step000479102`, about 14,600 steps lost (owner's note).
  - The owner then **rebooted the PC** (15:06). The supervisor resumed the run at 15:11:34 from
    `epoch014-step000515956` (`supervisor.log`); it trains at ~1.25-1.31M pos/s (`.resume2.log`).
  - I killed nothing and touched nothing under `F:\forge_nnue_train`.
- Rules since (owner, 15:16), all followed below:
  - free RAM is checked **during** every run and my job aborts itself below 7 GB;
  - only smoke-size runs (no L1 1024, no batch 16384, 1 loader worker);
  - stop my job first if the live trainer slows or memory gets tight.
  - The owner then allowed 50 min of GPU time. I used ~5 min of it (15:21:30-15:26:20) for the final clean runs.
- New tool: `tools/nnue_pytorch_amd/guard/guard_exec.py`. It runs a script in-process; a watchdog polls free RAM
  every 0.25 s and calls `os._exit(97)` below the floor; it logs the minimum free RAM and its own peak. The abort
  path was self-tested (exit 97). Every run after the reboot went through it (`logs/guard_runs.jsonl`): the
  minimum free RAM was 8.77 GB and the own peak 4.56 GB (full features) / 2.5-3.5 GB (smoke).

## Where things are
- Port, GPL-3.0, derived from nnue-pytorch b2614500: `tools/nnue_pytorch_amd/`
  - `patches/` (4 `git format-patch` files) and `src/` (the changed files at their repo paths)
  - `bench/`, `guard/`, `debug/`, `loader/`, `logs/`
  - `README.md`, `IDEA_SOURCE.md`, `LICENSE` (GPL-3.0 text from nnue-pytorch)
  - `SKILL_forge-nnue-pytorch-amd.md` (copy of the project skill)
- Working clone: `F:\opus_scratch\r6\nnue-pytorch-amd`, branch `opus-r6-amd` (4 commits on b2614500).
  `F:\nnue_pytorch\repo` is **not modified**. Grok Bot works there in parallel; it installed `triton-windows`
  and `rocm-sdk-devel` into the venv at 13:25 / 13:28.
- Apply: `cd <b2614500 checkout> && git am <branch>/tools/nnue_pytorch_amd/patches/000*.patch`
- **Must-know:** activate the venv (or `source tools/nnue_pytorch_amd/env.sh`) for **every** run. Triton's AMD
  driver needs `rocm-sdk` on PATH; otherwise it fails with `'hip/hip_runtime.h' file not found`
  (`logs/triton_without_venv_on_PATH.log`).
  - The R6 kernels then fall back to torch (one-time probes).
  - **torch.compile has no such fallback.** Inductor needs Triton, so a run without the venv on PATH fails at
    the first compiled step (Grok Bot's 13:25 `COMPILE_FAIL`) unless `TORCHDYNAMO_DISABLE=1` is set.
  - Upstream's Triton loader transport (`_cuda_transport.py`) is not affected: `_transport.move_indices` packs
    only when `torch.version.hip is None`, so on ROCm it never runs. An earlier version of this report said
    otherwise; that was wrong.

## Flags
| env var | values | default |
|---|---|---|
| `NNUE_FT_BACKEND` | `auto`, `triton`, `triton-sparse`, `torch`, `fused`, `sparse` | `auto`: CuPy if present (upstream unchanged), else Triton if the probe kernel passes, else `torch` |
| `NNUE_RANGER_FUSED` | `1` / `0` | `1`: without CuPy, Triton fused RangerLite if its probe passes; `0` = Python update path |
| `NNUE_DATA_LOADER_LIB` | path to a loader DLL | unset = upstream glob (newest file wins) |
| `NNUE_TRITON_BLOCK_C`, `_KC`, `_WARPS`, `_POS` | FT kernel tuning | 128 / 16 / 4 / 8 |
| `TORCHDYNAMO_DISABLE=1` | turns off torch.compile | compile on. It works now; use `TORCHINDUCTOR_COMPILE_THREADS=1` for the thread budget |

## J1: what was ported
| upstream CuPy kernel | Triton replacement | status |
|---|---|---|
| `fused_ft_kernel.py` fused double-perspective FT fwd + scatter bwd (fp32 atomics) | `triton_ft_kernels.py` `_fused_fwd_kernel`, `_fused_bwd_kernel` | done, J2 PASS |
| `sparse_linear_kernel.py` sparse linear fwd/bwd | `_sparse_fwd_kernel`, `_sparse_bwd_kernel` | done, J2 PASS |
| `ranger_lite.py` `_RangerLiteFusedKernels`: pnm/adam full, variance, pnm/adam phase 2 | `ranger_lite_triton.py`, 5 kernels | done, test PASS |
| `aggregated_ft_kernel.py` | not needed (NVIDIA-only upstream) | n/a |
| `grouped_linear.py` grouped L1 | not ported (NVIDIA-only upstream; dense path used) | open, see "Not done" |

Findings:
- **Triton works** on gfx1100 under Windows ROCm with triton-windows 3.6.0.post26 once the venv is on PATH.
  Smoke test: add, fp32 `atomic_add`, 2-D gather (`logs/triton_smoke_r6.log`). That also enabled torch.compile.
- **Bug: `tl.sqrt_rn` returns NaN for every fp32 denormal input on gfx1100** (`tl.sqrt` flushes to 0; torch is
  exact). See `logs/denormal_probe.log`.
  - Effect: the first RangerLite port went NaN in real training. `variance_ma` ~ g^2 * 1e-3 is denormal once
    |g| ~ 1e-19.
  - Found with a shadow optimizer (`debug/nan_hunt4.py`): the real fused step and the Python step on cloned
    state, compared every step. At step 112 one output-layer weight was NaN (fused) vs 0.063 (Python), with
    grad 5.9e-19.
  - Fix: flush denormals before `sqrt_rn`. Covered by a denormal test case and a planted-bug run (old kernel:
    6/6 denormal cases FAIL; fixed: PASS).
  - Wrong turns, so nobody repeats them: a stream race was suspected first. Clean "serialized" and
    "host-wait" runs were luck, because batch order varies between runs.
- Robustness: both new paths run a tiny probe kernel once per device and fall back to torch / Python with a
  warning if Triton cannot launch. A test injects a launch failure and checks for a warning and a result
  bit-identical to the Python path.

## J2: correctness
`src/tests/test_amd_triton_ft.py`: random sparse batches, unique indices per row, -1 padding (incl. mid-row
holes), us/them 0/1, weights 0.3*randn so the clamp hits both 0 and max, grad_out = randn/batch. Max abs diff vs the
torch backend:

| case (batch, active, inputs, L1) | path | fwd | grad_w | grad_b |
|---|---|---|---|---|
| tiny-odd (7, 5, 50, 96) | double / sparse | 6.0e-08 / 1.2e-07 | 1.5e-08 / 0 | 3.0e-08 / 6.0e-08 |
| holes (33, 12, 300, 128) | double / sparse | 2.4e-07 / 3.6e-07 | 1.1e-08 / 1.5e-08 | 2.2e-08 / 6.0e-08 |
| k32h3-l256 (4096, 32, 73728, 256) | double / sparse | 9.8e-07 / 1.9e-06 | 4.7e-10 / 2.3e-10 | 1.0e-08 / 2.7e-08 |
| k32h3-l1024 (1024, 32, 73728, 1024) | double / sparse | 9.8e-07 / 1.9e-06 | 1.9e-09 / 9.3e-10 | 2.2e-08 / 3.0e-08 |
| collide (2048, 32, 64, 256) | double / sparse | 7.7e-07 / 1.9e-06 | 1.5e-08 / 4.5e-08 | 9.3e-09 / 3.0e-08 |
| full288-l1024 (256, 288, 138096, 1024) | double / sparse | 7.2e-06 / 1.2e-05 | 2.7e-08 / 3.7e-09 | 3.2e-08 / 4.5e-08 |

- Stress (grad_out = randn, relative error vs float64): Triton 5.6e-07 / 2.1e-07 / 6.4e-07, torch fp32
  7.9e-07 / 1.1e-07 / 1.3e-07.
- After the reboot, re-run in `--small` mode (L1 <= 256 cases only, per the new rule): all PASS
  (`logs/j2_test_run3_small.log`).
- RangerLite (`src/tests/test_amd_triton_ranger.py`): paths A / B / A+wd, pnm on and off, normal and denormal
  gradients. The kernel-call counters prove which path ran. Max abs diff <= 3.6e-07, plus the fallback check
  -> PASS (`logs/j1_ranger_test_run5.log`).

## J3: speed
### Final clean A/B, 15:22-15:26 (after the reboot, smoke size, every run under the RAM guard)
Command as in the 210k baseline: `train.py .pgo/small.binpack --features K32H3^ --l1 256 --accelerator cuda
--batch-size 4096 --epoch-size 204800 --max-epochs 10 --threads 2 --num-workers 1`. pos/s per epoch comes from
epoch-end timestamps; the table shows the median of the 9 timed epochs (`logs/final_bench/`).

| run | FT | optimizer | torch.compile | median pos/s |
|---|---|---|---|---|
| A1 / A2 (the setup's config) | torch | Python | off | 196,467 / 220,740 |
| B | Triton | Python | off | 283,390 |
| C | Triton | Triton | off | 347,783 |
| D | torch | Python | on | 328,011 |
| **E1 / E2 (final)** | Triton | Triton | on | **447,693 / 466,517** |
| F1 full features (Full_Threats+PP_3Wide+K32H3^, L1 256, 8 epochs) | torch | Python | off | 34,757 |
| **F2 full features** | Triton | Triton | on | **277,281** (8.0x) |

- Final config vs the 210k reference: 2.13x / 2.22x.
- Step breakdown with synced timers (`logs/final_bench/P_profile_final.log`), before -> after
  (Triton FT only, eager -> all Triton + compile):

  | phase | before | after |
  |---|---|---|
  | forward+loss | 6.6 ms | 2.2 ms |
  | backward | 5.4 ms | 4.1 ms |
  | optimizer | 5.25 ms | 1.9 ms |
  | loader / H2D / Python | 4.4 ms | 4.0 ms |

  The loader/H2D/Python share is now the largest (33%).
- Before the incident (no guard; kept in `logs/bench/`):
  - FT layer alone, synthetic: 4.6x at the smoke shape, 2.2x at B 16384 / L1 1024, 1.8x at 288 features /
    L1 1024.
  - `c2` (L1 1024, batch 16384): 155k -> 338k pos/s (2.18x). **This size is now forbidden while the live trainer
    runs**; it is the run that crashed it.
- The live trainer reported 1.30-1.31M pos/s during ep17 and ~1.25M during ep18 (epoch-to-date averages; epoch
  starts dip). My final runs overlapped ep18, so they probably cost it a few percent for ~5 minutes, inside the
  allowed GPU window.

## J4: Windows loader and end-of-run crash
- **Crash fixed.** `train.py:452 dist.is_initialized()` -> `dist.is_available() and dist.is_initialized()`, the
  same guard the rest of the code base uses. Runs exit 0 and write `training_finished` + `last.ckpt`;
  `serialize.py` exports a 17.6 MB .nnue (`logs/j4_serialize.log`).
- **Loader.** Full details and merge notes: `tools/nnue_pytorch_amd/loader/LOADER_NOTES.md`.
  - CMake: `NNUE_BMI2=AUTO|ON|OFF`, Windows BMI2 auto-detection, MSVC-style flags.
  - Builds: g++ BMI2 1.06x, g++ PGO 1.08x, AMD clang 23 (ROCm SDK, MSVC ABI, static CRT) **1.88x** per thread.
  - Features from fixed FENs are bit-identical across builds. The clang/MSVC stream shuffles in a different
    order (`std::shuffle` is implementation-defined); the first window holds the same position multiset.
  - No training gain at smoke size, re-checked with the final config at 15:33 (guarded, 1 worker,
    alternated): setup DLL 446,637 / 447,308 vs clang DLL 446,737 / 446,914 pos/s
    (`logs/final_bench/G*_final_setupdll.log`, `H*_final_clangdll.log`). One worker already delivers the K32H3
    batches faster than the GPU consumes them. The 4 ms/step "loader/H2D/Python" share is transfer and per-step
    Python overhead, not loader compute. The faster DLL matters for heavier feature sets and for more data per
    worker.

## Not done / open
- Grouped-L1 kernel. Upstream gates it to NVIDIA (`torch.version.hip is None`). It replaces a dense
  B x L1 x (32 x out) matmul and pays off only at L1 >= 1024, which may not be run while the live trainer runs.
  At L1 256 the dense layer is a small part of the 2.2 ms forward. Left undone as instructed.
- Full-feature benchmark at upstream sizes (L1 1024): not run (forbidden size). The small-size pair F1/F2 was run.
- Real `cl.exe` builds of the loader are untested (only clang++ with an MSVC target). No clang PGO (no matching
  `llvm-profdata`).
- torch.compile has no fallback when Triton cannot launch (venv not on PATH); see "Must-know".
- FT kernel tuning knobs exist but the sweep was not run (FT is no longer the bottleneck at smoke size).
- Next bottleneck: loader/H2D/Python at 4 ms/step. More loader workers would help but cost CPU threads
  (budget 3).

## Timeline (from commit timestamps, PC clock)
- 13:24 start. Branch commits 13:29 -> 15:26: 8 pushes, plus 4 commits in the clone (13:37, 14:05, 14:24, 15:21).
- Down time: 14:46 -> 15:16 (incident, owner restart, reboot).
- Push cadence missed the 10-minute rule three times during the NaN hunt and the loader work (gaps of ~20 min:
  13:46-14:06, 14:06-14:25, 14:25-14:45).

## Licence
nnue-pytorch is GPL-3.0, and so is everything in `tools/nnue_pytorch_amd/` (`LICENSE` included). Nothing was
copied into Forge engine sources (`IDEA_SOURCE.md`).
