---
name: forge-nnue-pytorch-amd
description: Running and changing Stockfish's nnue-pytorch trainer (GPL-3.0) on the PC's AMD RX 7900 XT under Windows ROCm - venv and PATH needed for Triton, the R6 Triton ports of the CuPy kernels (feature transformer, sparse linear, RangerLite), flags NNUE_FT_BACKEND / NNUE_RANGER_FUSED / NNUE_DATA_LOADER_LIB, correctness tests, the short-training benchmark and NaN-hunt tools, native loader builds (MinGW g++, AMD clang 23 MSVC ABI), pitfalls (tl.sqrt_rn denormal NaN, Grok Bot working in the same folder, live DirectML trainer on the same GPU). Use for any task that touches F:\nnue_pytorch, branch opus-r6-amd-nnue, tools/nnue_pytorch_amd, Triton/ROCm on this PC, or GPU NNUE training speed.
---

# nnue-pytorch on the AMD GPU (R6, 2026-10-29)

Rules first: [[forge-pc-rules]]. Licence: nnue-pytorch and every patch to it are **GPL-3.0**. They stay in
`F:\nnue_pytorch`, the scratch clone, or `tools/nnue_pytorch_amd/`, and never go into Forge `src/`, `include/` or
`tests/`. Write an IDEA_SOURCE note when an idea moves over.

## Where things are
- Trainer install (setup by Grok Bot): `F:\nnue_pytorch\repo` (pinned b2614500), venv `F:\nnue_pytorch\venv`
  (py 3.12, torch 2.11.0+rocm7.13.0, triton-windows 3.6.0.post26, rocm-sdk-devel 7.13.0), `SETUP_REPORT.md`.
- R6 port: clone `F:\opus_scratch\r6\nnue-pytorch-amd`, branch `opus-r6-amd` (3 commits). The same changes are
  in branch `opus-r6-amd-nnue`, folder `tools/nnue_pytorch_amd/` (`patches/*.patch`, `src/`, `bench/`, `debug/`,
  `loader/`, `logs/`). Report: `docs/OPUS_R6_AMD_NNUE.md`.
- Applying to a b2614500 checkout: `git am tools/nnue_pytorch_amd/patches/000*.patch` (or copy `src/`). Copy a
  loader DLL to `build/` or set `NNUE_DATA_LOADER_LIB`.

## Environment (every run)
`source tools/nnue_pytorch_amd/env.sh` (or `F:\opus_scratch\r6\tools\env.sh`). It puts the venv `Scripts` folder
on PATH. **Triton needs this**: its AMD driver gets the HIP include dir from `rocm-sdk path --root`. Without
it, the build fails with `hip_utils.c: fatal error: 'hip/hip_runtime.h' file not found` (Grok Bot's 13:25
failure). env.sh also sets the thread caps, TMP, `TRITON_CACHE_DIR` and `TORCHINDUCTOR_CACHE_DIR` under scratch.
Always add `TORCHINDUCTOR_COMPILE_THREADS=1` (inductor otherwise spawns a worker per CPU) and run under `nice -n 10`.
Without the venv on PATH:
- the R6 kernels fall back to torch (probes), but torch.compile fails (no fallback; use `TORCHDYNAMO_DISABLE=1`);
- the loader transport does not use Triton on ROCm (`move_indices` packs only when `torch.version.hip is None`).

Run every torch job through `tools/nnue_pytorch_amd/guard/guard_exec.py` (`F:\opus_scratch\r6\tools\guard_exec.py`).
It is an in-process RAM watchdog that calls `os._exit(97)` below `R6_MIN_FREE_GB` (7) and logs the minimum free
RAM and its own peak. `R6_EPOCH_TIMER=1 R6_EPOCH_SIZE=<epoch size>` prints pos/s per epoch.
`bench/final_bench.sh k32|full` is the guarded final A/B set.

## Flags
- `NNUE_FT_BACKEND`: `auto` = CuPy if present, else Triton if a probe kernel passes, else torch. Other values:
  `triton`, `triton-sparse`, `torch` (plain fallback), `fused`, `sparse`.
- `NNUE_RANGER_FUSED=0` keeps RangerLite's Python update path. The default uses the Triton fused kernels
  without CuPy.
- `NNUE_DATA_LOADER_LIB=<dll>` picks the loader DLL. Otherwise the newest `build/**/*training_data_loader.*` wins.
- `TORCHDYNAMO_DISABLE=1` turns off torch.compile. It works now that Triton works, and is worth ~1.3-1.45x.

## Tests (each runs seconds on the GPU)
- `python tests/test_amd_triton_ft.py`: FT fwd/grad vs the torch path, 12 cases + float64 stress.
  PASS = < 1e-4 (measured worst 1.2e-5).
- `python tests/test_amd_triton_ranger.py`: fused vs Python RangerLite, paths A / B / A+wd, normal and denormal
  grads, with kernel-call counters.
- `debug/planted_sqrt_bug.py` must report "PLANTED BUG DETECTED".

## Memory budget (read before any run)
On 2026-10-29 at 14:29 the live Forge trainer (13 GB private) died with a numpy allocation error during
`c2_triton` (L1 1024, batch 16384, 2 workers, compile). The smoke config (K32H3^, L1 256, batch 4096, 1 worker)
ran ~25 times without trouble. While the live trainer runs, stay at smoke size. For anything bigger, measure
the peak first (Process.PrivateMemorySize64 sampled during the run) and require free RAM >= 6 GB + that peak.

## Benchmark recipe (J3)
`python bench/bench_train.py NAME [ENV=VAL ...] -- .pgo/small.binpack --features K32H3^ --l1 256 --accelerator cuda
--batch-size 4096 --epoch-size 204800 --max-epochs 10 --threads 2 --num-workers 1`
- Output: `F:/opus_scratch/r6/bench/NAME/result.json`, pos/s per epoch from epoch-end timestamps.
- The runner refuses to start below 6 GB free RAM. Take the median of epochs 2..N, and always A/B in the same
  session: the GPU is shared with the live trainer, so absolute numbers move ±20%.
- R6 final numbers (15:22-15:26, guarded, smoke size):
  - torch eager 196k / 221k (= the 210k reference); Triton FT only 283k; Triton all, eager 348k;
    torch + compile 328k; **Triton all + compile 448k / 467k**.
  - Full features at L1 256: 35k -> 277k.
  - Breakdown after: forward 2.2, backward 4.1, optimizer 1.9, loader/H2D/Python 4.0 ms/step. The loader side is
    the next bottleneck.
- `bench/profile_train.py` gives a synced per-phase breakdown. Note that train.py ends with `os._exit(0)` on
  win32, so the atexit report only prints when main() raises: patch `os._exit` or call main() yourself.

## Forge v2 nets on the fast path (R7 J1, branch opus-r7-speed, `tools/nnue_pytorch_amd/forge_v2/`)
- `train_forge_v2_fast.py --backend triton --fused-adam 1 --pinned 1 --inflight 3 --batch 4096 --threads 1`:
  Forge's FORGENN2 shape (32 mirrored king buckets x 768, H 256, SCReLU, 8 output buckets), K32H3 loader indices
  remapped inside the Triton kernel, export through Forge's `tools/nnue/forge_nnue_v2.py`
  (`FORGE_V2_WRITER`, default the opus-r7-nps worktree). Env: `source F:/opus_scratch/r7/tools/env_r7.sh` (sets
  NNUE_REPO = the R6 clone, NNUE_DATA_LOADER_LIB, caches, R6_MIN_FREE_GB=7, $GUARD).
- Numbers (batch 4096, 1 loader thread): Grok Bot's plain `train_forge_v2.py` 363k pos/s, plain in the same harness
  386-396k, Triton + fused Adam ~0.9-1.0M, **+ pinned H2D 1.44M**; GPU-only ceiling 1.5M; loader alone 3.7M (setup
  DLL) / 5.1M (clang23 DLL). Pinned without `--inflight` held +0.75 GB host memory.
- Checks: `test_forge_v2_kernels.py <binpack>` (Triton == plain, 2 planted errors), `parity_forge_v2_fast.py` vs
  `nnue_v2_tool eval` (built from the engine tree with the exe's flags; max 1.59 cp on 10k), `engine_load_check.py`
  (shape options before NNUEFile; transient ERROR lines before NNUEFile are expected).
- Binpack from Forge `.pos`: `tools/nnue_pytorch_amd/fpos2sf_mt/` (byte-identical to Grok Bot's fpos2sf, 3 threads);
  the dummy king move becomes `Move::null()` in binpack: never use the loader's `filtered=True` on these files.

## NaN / divergence hunting (method that worked)
1. `debug/nan_hunt.py`: first non-finite batch/grad/param per step.
2. `debug/nan_hunt4.py`: shadow optimizer. Clone params, grads and state, run the real fused step, then the
   Python step on the clones, and compare. It names the tensor, the element and its gradient.
3. Do not conclude "race" from a clean serialized or host-wait run: batch order varies between runs, so short
   clean runs are weak evidence. Repeat with the compiled model (it diverges earlier).

## Pitfalls seen
- **`tl.sqrt_rn` returns NaN for fp32 denormals on gfx1100** (`tl.sqrt` flushes to 0). Flush first:
  `tl.sqrt_rn(tl.where(x < 1.1754943508222875e-38, 0.0, x))`. Any new Triton kernel with sqrt/rsqrt of small
  values needs this. Probe: `debug/denormal_probe.py`.
- Triton jit code can only read globals that are `tl.constexpr(...)`.
- Grok Bot (the PC's own agent, parent `Grok Bot.exe`) works in `F:\nnue_pytorch` at the same time and installs
  packages into the venv. Use your own clone, use the venv read-only, and check
  `Get-CimInstance Win32_Process | ? CommandLine -match 'nnue_pytorch|uv.exe'` before relying on the venv.
- Files in the clone are CRLF (core.autocrlf=true). Patch scripts must normalise `\r\n`. Write Python patch
  scripts with the Write tool (heredocs mangle `\n`).
- Commit identity: `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit ...`
  (no global identity is configured). A new worktree from origin/main tracks main: run
  `git branch --unset-upstream` and push with an explicit branch name.
- Loader builds (`loader/build_loader.sh <variant>`):
  - MinGW g++ needs `C:\msys64\ucrt64\bin` on PATH (silent compiler failure otherwise).
  - A static DLL needs `-Wl,--exclude-libs,ALL`, otherwise `_Unwind_Resume` / `__gcov_*` are defined twice.
  - Never put `-static` on the exe link.
  - LLVM 18 cannot compile against the MSVC 14.51 STL (STL1000). Use the ROCm SDK clang 23:
    `F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_core\lib\llvm\bin\clang++.exe`, ~1.9x faster per thread.
    There is no matching llvm-profdata, so no clang PGO.
  - `std::shuffle` order differs between libstdc++ and the MSVC STL (implementation-defined). Check equality with
    `loader/dl_equal.py` modes `fens` (bit-identical) and `window` (same multiset in the first window).
- The live Forge trainer (`train_res*_v3b.py`, torch-directml) uses the same GPU. Keep GPU runs to seconds or
  minutes and check its `pos/s` lines in `F:\forge_nnue_train\runs\<run>.log`, plus the supervisor
  "adopted running job" count (7), before and after.

## R10 (2026-10-30): nets for Forge's EvalFileHalfKA (branch opus-r10-halfka)
- This trainer version (b2614500) has no HalfKAv2_hm: the king feature set is `K32H3^` (32 mirrored king buckets x 3
  material states, FT weights int8); Forge's `EvalFileHalfKA` loads K32H3^-only nets (any L1 multiple of 64, L2/L3 <= 64)
  and rejects Full_Threats / PP_3Wide nets with a message. Exact parity method: [[forge-halfka-parity-test]].
- CPU smoke training (no GPU): `cd <clone>; NNUE_FT_BACKEND=torch TORCHDYNAMO_DISABLE=1 OMP_NUM_THREADS=2 <venv python>
  -B run_pinned.py --mask 0x0FF0 -- guard_exec.py train.py <binpack> --features "K32H3^" --l1 64 --accelerator cpu
  --batch-size 4096 --epoch-size 200000 --max-epochs 8 --threads 2 --num-workers 1 --no-filtered --no-wld-filtered
  --default-root-dir <dir> --save-last-network True` (~10k pos/s, ~20 s per 200k epoch). It holds 5.1-5.4 GB private
  memory whatever the binpack size: the 7 GB guard ended both R10 runs (after epoch 5 the second time).
- Export: `PYTHONPATH=<clone> <venv python> -B run_pinned.py --mask 0x0FF0 -- serialize.py <last.ckpt> <out.nnue>
  --features "K32H3^" --l1 64` (PYTHONPATH is needed under run_pinned/runpy).
- An untrained net of any size for load/NPS tests: `opus_r10/tools/make_init_net.py <out> --l1 1024` (NNUEWriter).

## R11 (2026-10-30): trainer behaviour that matters for automation - see [[forge-nnue-pipeline]]
- b2614500 uses its own SimpleTrainer (no Lightning): `--resume-from-checkpoint`, `--save-top-k` keeps the newest k
  periodic checkpoints but only those of the CURRENT process (after a restart older ones are never pruned),
  `--async-checkpoint-save` is ON by default (pass `False` before renaming files), `--validation-datasets` is an append
  option (one flag per file), `--check-val-every-n-epoch 1`.
- The epoch-end checkpoint is written in on_train_epoch_end, BEFORE the epoch's scheduler step and validation, with
  epoch=E; resume restarts at E (epoch E is trained twice). R11's entry saves at on_validation_end with
  `r11_next_epoch` = E + 1 and patches load_checkpoint to continue there.
- train.py ends with `os._exit(0)` only in `__main__`: calling `train.main()` from a wrapper returns normally; a NaN abort
  is `sys.exit(1)`. The batch loop never checks `should_stop` inside an epoch: stop mid-epoch by raising from a callback.
- The owner's queue runs nnue-pytorch through an adapter (`--npt-*` args, guard_exec.py, R6 clone, L1 1024 batch 16384,
  2 workers, 20 x 152.5M, lambda 1.0, lr 8.75e-4, `--network-save-period 2 --save-top-k 2`); exports via
  `serialize.py <ckpt> <out> --features=K32H3^ --l1=1024` with CUDA/HIP hidden (D:\forge_nnue_train\exports\npt_line104).
