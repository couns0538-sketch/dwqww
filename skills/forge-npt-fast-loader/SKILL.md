---
name: forge-npt-fast-loader
description: The R14-B fast data loader for the npt (nnue-pytorch) trainer on grok-pc - forge_fastloader.dll + .py behind --fast-loader (default off), how it reproduces the old loader's --num-workers 1 stream byte for byte, the build (pc1 = pc2), the equality harnesses (raw C API and the trainer's Dataset path), the self-test + CI sanitizers, the CPU loss match, the loader-only ABBA, the GPU-window request, the trainer installer, and the pitfalls hit on 2026-11-02. Use for any question or change about npt data loading speed, --fast-loader, the old loader's skip filter / shuffle semantics, or batch-equality proofs.
---

# forge-npt-fast-loader (Opus R14-B, branch `opus-r14b-fast-loader`, folder `opus_r14b/item1/`)

## What and why
- The live npt line (`F:\opus_scratch\r6\nnue-pytorch-amd\train.py`, adapter `F:\forge_nnue_train\tools\train_resid_nnuepytorch_v2.py`)
  loads `...\nnue-pytorch-amd\build\libtraining_data_loader.dll` (R6 "setup" g++ build, the slowest one). The run reads
  ~10 records for every one it trains on (piece-count filter rejects ~90 %); the J1 binpack is unchained (34 B/record).
- `forge_fastloader` filters on the packed record fields without building a board, shuffles a 4-byte index
  permutation instead of 224-byte entries, and builds feature batches on several threads (batch k -> slot k).
- Behaviour spec in own words: `LOADER_SPEC.md`. nnue-pytorch is GPL-3.0: read for behaviour only, never copy.

## The reference stream
- Old loader thread split (sparse stream): builders = max(1, floor(N/4)), decode workers = max(1, N - builders).
  N = 1 and N = 2 = one decode worker -> deterministic (filter state + mt19937_64 default seed + std::shuffle of each
  2^20 window all in one thread). N = 4 (live) = 3 racing decode workers -> not reproducible.
- "Bit-identical to the old loader" = against `--num-workers 1`; the fast loader gives that stream at any thread count.
- Seal timing matters: kept records go to a 16,384-entry scratch; a window seals (and shuffles, drawing from the same
  engine) only when a scratch flush fills it. Get this wrong and every later batch differs.

## Build and identity
- `fastloader/build_fastloader.sh OUT` (MinGW g++ 15.2 - the old DLL's libstdc++, so std::shuffle matches).
  Reproducible only with `-frandom-seed=... -Wl,--no-insert-timestamp -Wl,--disable-auto-image-base` (without them
  pc1 != pc2: link timestamp, GCC random symbol names, image base hashed from the output path).
- g++ needs `C:\msys64\ucrt64\bin` on PATH or it fails silently. Run builds through `tools/lowrun.ps1` (the
  PowerShell process lowers itself first, children inherit class + mask; pass program args with `-ArgLine`, because
  PowerShell eats `-o` as one of its own parameters).

## Proof recipe (all own tools, stdlib Python unless noted)
1. Raw equality: `tools/fl_equal.py dump --loader old|fast --dll ... --workers N --batches 1000 --out X.tsv`, then
   `compare A B` (refuses unhashed dumps or different settings). Hashes the 3n-float + 66n-int blocks = every byte the
   trainer reads. `--skip key=value,...` for other skip settings, `--batch/--window/--finite` for other shapes.
2. Trainer-path equality (trainer venv, GPU hidden): `tools/fl_dataset_equal.py` builds the streams exactly like the
   patched `make_data_loaders` (Dataset -> FixedNumBatchesDataset -> DataLoader) and hashes every tensor.
3. Self-test `fastloader/ffl_selftest.cpp` (own fixtures; independent no-filter reference; thread-count invariance;
   format errors; destroy while running; window < batch; acceptance 0; double release); CI workflow
   `.github/workflows/ffl-sanitize.yml` runs it under ASan+UBSan and TSan on Linux.
4. CPU loss match: `tools/lm_run.sh old|fast DIR` (copy it before running - see pitfalls); `LM_L1=256 LM_VAL=0` keeps
   the old arm above the 7 GB RAM floor.
5. Speed: `tools/fl_abba.py` (palindromic ABBA of loader-only runs; advisory; QA times officially).
6. GPU window: `GPU_REQUEST.md` (one epoch of the live recipe with --fast-loader; GPU util from the keeper's HWiNFO CSV).

## Trainer switch
`tools/install_fast_loader.py <trainer copy>` (exact anchors, keeps CRLF/LF, refuses a patched or changed trainer, unknown
arguments and a real install into the live trainer folder - exit 2; `tools/test_installer.sh` checks all of it, 25 cases, without ever sending an install to the live folder);
same as `patches/0005-fast-loader-switch.patch`. Loader files from `FORGE_FAST_LOADER_DIR` (or next to train.py),
loaded by explicit path; the start-up line prints the DLL path, sha256 and version. `--num-workers N` = N loader threads
(reader + filter + N-2 builders). Never patch the live trainer folder; Engine NNUE / QA decide about adoption.

## Pitfalls (2026-11-02)
- Never edit a bash script that is running (bash reads it by byte offset): editing `lm_run.sh` during a run shifted
  the resume point into the middle of a command. Run a private copy per run, with its helpers next to it.
- The old loader holds up to (consumers + 8) windows of 2^20 x 224 B per stream and reads ~10x ahead: L1 1024 + a
  validation stream on the CPU hit the 7 GB guard floor (own private 8.36 GB).
- `(1 - p) * 2^64` is out of range at p = 0; both DLLs saturate via AVX-512 `vcvttsd2usi`, a plain cast elsewhere
  gives 0. The fast loader saturates explicitly.
- `kill` / `Stop-Process` are blocked by the session permissions. TaskStop of a background task ends its outer shell
  only: a child started through `lowrun.ps1` (Start-Process) keeps running as an orphan until it finishes. Never
  count on TaskStop as a kill; wait for the orphan before starting the next CPU step (thread budget).
- Git Bash rewrites Windows switches that look like paths: `robocopy SRC DST /E` became `... E:/` (exit 16, nothing
  copied, 2026-11-02 chain). Prefix such calls with `MSYS_NO_PATHCONV=1` (or run them from cmd / PowerShell).
- No HIP runtime next to the live npt line: CPU tests hide the GPU with CUDA_/HIP_/ROCR_VISIBLE_DEVICES=-1.
- npt training is not reproducible run to run, independent of the loader: train.py builds the model before applying
  `--seed`, and torch 2.11.0+rocm7.13.0 seeds its default generator from the clock per process. An exact loss match
  needs `tools/lm_det.py` (seeds before train.py, deterministic algorithms) + `LM_THREADS=1`; the optional trainer
  fix is `patches/0006-seed-before-model-OPTIONAL.patch` (Engine NNUE decides).
- A dump with no batches must write no row (fixed 14:25): an empty line once counted as a "batch" in `compare`.

## Measured (2026-11-02, b5 9eb29b7d, ADVISORY - QA does official timing)
- Equality: 1000/1000 train + 300/102 validation batches; trainer path 261/261 (every tensor); config matrix 24/24;
  3,100 batches of 10,000 (spanning windows) past the first file wrap; exact CPU loss match (5/5 logged values).
- Loader-only ABBA (10 pairs, CPUs 2-3, same 3-thread layout): old 468k vs fast 4.04M kept positions/s = 8.65x.
  Live thread setting (old `--num-workers 4` vs fast 2 builders): 6.25x on CPUs 2-3 (772k vs 4.82M), 7.19x on ONE
  logical CPU (408k vs 2.91M): 2.45 vs 0.34 CPU-us per kept position; feeding the live line (121k-169k kept / s)
  takes 0.30-0.41 of a CPU with the default loader, 0.04-0.06 with the fast one.
- The live line's GPU use with the default loader (keeper's HWiNFO log, `opus_r14b/tools/gpu_util_stats.py` on
  opus-r14b-status): 15:14-21:14 mean 45.7 %, >= 90 % in 4 % of samples - the before figure for the GPU window.
- Damaged files (`tools/fl_fuzz.py`, 371 runs incl. a `-D_GLIBCXX_ASSERTIONS` build): clean errors, no crash, no hang.
  Shared limit with the default loader: a cyclic stream over a file in which nothing passes the skip filter waits.
- A full trainer epoch (152.5M positions, 1.55 B records) through the fast loader alone: 29.8 s, 166 MB peak.
- CPU training on 2 CPUs: 11.4 vs 40.2 min for the same 64 batches (old loader threads starve torch); peak private
  4.1 vs 6.2 GB.
- Distribution vs the live layout (old loader `--num-workers 4`, not reproducible) over 2,000 batches = 32.8M positions
  each (`tools/fl_distribution.py stats` + `compare`): total-variation distance < 0.001 for piece count, side to move,
  outcome, queen bucket and score histograms; mean score -1.17 SE. Same distribution, different sample.

## Handing it over (opus_r14b/item1/HANDOFF.md)
- Adoption without touching crew code: the adapter `train_resid_nnuepytorch_v2.py` already takes `--npt-repo <copy>`
  and `--npt-extra ...` (REMAINDER, so it goes last): `--npt-repo <switched copy> ... --npt-extra --fast-loader`.
- Install into a COPY of the trainer: `python -I -B tools/install_fast_loader.py <copy> --loader-dll <built DLL>`
  switches config.py / train.py and copies forge_fastloader.dll + forge_fastloader.py next to train.py (never over an
  existing file; a second install is exit 2; `--check` = dry run that prints "would copy"). Check the copy first
  against `trainer_manifest_b2614500.sha256` (`sha256sum -c`, 264 files).
- Acceptance check before any GPU run: `bash tools/fl_acceptance.sh <trainer copy> <new out dir>` (CPU only, GPU
  hidden, ~1 min: old w1 36 s, fast w4 6 s; 261 / 261 batches of every tensor identical on D:\o14b\npt). With only
  those two arguments it uses the copy's own `build\libtraining_data_loader.dll` (old) and the loader files next to
  its train.py (fast), i.e. exactly what an installed copy will run.
- `--num-workers N` = N - 2 builder threads (min 1) + reader + filter; `--num-workers 3` already gives ~24x the live
  line's consumption. The live tree still matched the installer's base copy (264 / 264 files) on 2026-11-02 16:04.
