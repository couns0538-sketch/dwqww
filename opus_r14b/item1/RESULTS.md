# R14-B item 1 - fast npt data loader (`--fast-loader`, default off) - DONE except the GPU window (requested), UNPROVEN

Branch `opus-r14b-fast-loader` (from main). Own code; the npt loader (nnue-pytorch, GPL-3.0) was read for behaviour
only (IDEA_SOURCE.md). Nothing of the live npt line was touched: the reference DLL is a copy, the trainer copy lives
in `D:\o14b\npt`. No Elo or training-quality claim; Engine NNUE / QA decide.

## Candidates
| build | DLL sha256 | status |
|---|---|---|
| b4 (12:37) | a4f965aa075f623311c5deb3a41cfa01131320dd4adf72c617f7c0f0adb2e733 | superseded by b5 (review fixes); its equality evidence is kept in logs/equality |
| **b5 (13:39)** | **9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935** (`D:\o14b\fl\b5`, `b5pc2` byte-identical = pc1 = pc2; installed with the new wrapper in `D:\o14b\fl\b5_install`) | current candidate |

Build: `fastloader/build_fastloader.sh OUT` (MinGW g++ 15.2 = the old DLL's toolchain, `-O3 -march=znver5`, static,
fixed random seed, no link timestamp, no auto image base), BelowNormal on CPUs 2-3. Reference: copy of the queue's
DLL `F:\opus_scratch\r6\nnue-pytorch-amd\build\libtraining_data_loader.dll` -> `D:\o14b\ref\` (sha256 88c01468...939c).
Trainer switch: `tools/install_fast_loader.py <trainer copy>` (= `patches/0005-fast-loader-switch.patch`); with the
switch on, the trainer prints `Fast loader: ON (<version>, <DLL path>, sha256 <...>)`.

## Checks
| check | result | evidence |
|---|---|---|
| reference deterministic: old `--num-workers 1` twice, and `--num-workers 2` (same 1 decoder + 1 builder) | 1000 / 1000 identical each | logs/equality/eq_old_w1*.tsv, eq_old_w2.tsv |
| train file, first 1,000 batches (16,384,000 positions), b4 at 1 / 2 / 4 builder threads vs old w1 | **1000 / 1000 identical** (sha256 of the float and int blocks = every byte the trainer reads, plus size and active counts) | logs/equality/b4_fast_t*.tsv |
| validation file: 300 batches cyclic (three wraps) / finite stream to end of file (last batch 9,582) | 300 / 300 and 102 / 102 identical; read 16,388,575 / kept 1,664,366 in both | logs/equality/*val* |
| self-test (independent no-filter reference, thread-count invariance, row invariants, 7 format errors, destroy while running, window < batch, acceptance 0, double release) | b5: ALL PASSED locally (`_GLIBCXX_ASSERTIONS`) and in CI under ASan+UBSan and TSan (runs 41441092765 for b4, 41446915233 for b5) | `fastloader/ffl_selftest.cpp`, `.github/workflows/ffl-sanitize.yml` |
| **trainer path: old SparseBatchDataset (w1) vs FastSparseBatchDataset b5 (w4), through FixedNumBatchesDataset + DataLoader, every tensor (8 per batch)** | **261 / 261 batches identical (200 train + 61 validation)** | logs/dataset/ds_*.tsv (`tools/fl_dataset_equal.py`) |
| CPU loss match at 2 threads (K32H3^ L1 256, 64 batches, seed 5117, no validation stream): old arm (old DLL w1) vs fast arm (b5 + installer patch, `--num-workers 2 --fast-loader`) | losses NOT equal (epoch 0.016163233667612076 vs 0.016393575817346573; step 13 0.019647 vs 0.019793) although the trainer receives identical tensors (row above): 2-thread CPU training is not bit-reproducible -> deterministic pair below. Fast arm 11.4 min vs old 40.2 min on the same 2 CPUs (the old loader's threads take CPU from torch); peak private RAM 4.08 vs 6.2 GB; no RAM-floor trip | logs/lossmatch/ |
| CPU loss match, deterministic attempt 1 (1 thread, `torch.use_deterministic_algorithms`, 16 batches): fast twice | **fast vs fast also differs** (epoch 0.020004266873002052 vs 0.02009074203670025) -> the trainer itself is not reproducible: see "Finding for Engine NNUE" below | `D:\o14b\lm\det3_*` |
| **CPU 1-epoch loss match, reproducible setup** (K32H3^ L1 256, epoch = 16 batches of 16384, seed 5117 set before the model is built, 1 thread, `torch.use_deterministic_algorithms`; `tools/lm_det.py`): fast (b5, `--fast-loader --num-workers 2`) twice, old (`--num-workers 1`) once | **EXACT MATCH: old = fast = fast on all 5 logged values** (steps 4 / 8 / 12 / 16: 0.02027221769094467, 0.020174967125058174, 0.01979747787117958, 0.02008046768605709; epoch 0.02009364403784275); no RAM-floor trip (peak private old 6.13 GB, fast 4.01 GB) | logs/lossmatch/det4_* |
| **b5 vs old, standard config**: train 1000 batches (b5 at 2 and 4 builders), validation 300 cyclic + 102 finite | **all identical** | logs/b5checks/std_*.cmp |
| **b5 vs old, config matrix** on the self-test's synthetic files (60,000 records with random plies, VALUE_NONE and zero scores; 30,000 records with 2-7 pieces), each cyclic (120 batches) and finite: npt defaults, no filter at all, random skipping 3, early skipping 8, `pc_y1=0` (acceptance 0), `ply_y1=0`, other spline values, window 1024 < batch 5000, batch 16384 with a 2^20 window | **24 / 24 identical** (the 2-7-piece file with `pc_y1=0` keeps 0 of 30,000 positions in both) | logs/b5checks/syn_*.cmp, low_*.cmp, matrix_settings.txt |
| **b5 vs old, real data, batch 10,000** (batches span shuffle windows), 3,100 batches = past the first wrap of the 10.4 GB train file | **3100 / 3100 identical** | logs/b5checks/real_b10000.* |
| trainer path again inside the check run (b5, w4 vs old w1) | 261 / 261 identical | logs/b5checks/ds_* |
| **speed: palindromic ABBA, 10 pairs, CPUs 2-3, BelowNormal, same 3-thread layout** (old w2 = reader + decoder + builder; fast = reader + filter + 1 builder), 420 batches, 20 warm-up | **old median 468,494 vs fast 4,035,567 kept positions/s: 8.65x (mean 8.64x, 95 % CI 8.58 .. 8.69)** - ADVISORY, QA times officially | logs/b5checks/abba/summary.txt |
| **one full trainer epoch through the fast loader alone** (9,307 batches = 152.5M positions; 1.55 B records read) | **29.8 s** (5.13M positions/s on 2 CPUs), peak working set **166 MB** flat over the epoch (the live line needs 16-20 min of GPU time per epoch) | logs/b5checks/full_epoch_fast.tsv |
| GPU window epoch | REQUESTED, NOT GRANTED during R14-B (the npt queue holds the GPU until 2026-11-08; GPU util 47.7 % at 13:53) - GPU_REQUEST.md is ready for Engine NNUE / QA | GPU_REQUEST.md |

## Done criteria (Couns) - status
| criterion | status |
|---|---|
| pushed and CR-ready | yes: code, spec, installer + patch, tests, CI, logs on `opus-r14b-fast-loader` |
| first 1,000 batches bit-identical, same data, same seed | yes (reference = old `--num-workers 1`, the only reproducible old stream; also b5 vs old on 24 other configurations, 3,100 spanning batches past a wrap, and 261 batches through the trainer's own data path) |
| 1-epoch loss matches exactly | yes, in a reproducible training setup (CPU, 1 thread, deterministic algorithms, seed before the model). With the trainer as it is, no two runs match even with the same loader (finding below) |
| >= 3x positions/s on 2 CPU threads (or >= 90 % GPU use) | yes: 8.65x (ADVISORY ABBA); the GPU-use measurement needs the window |
| no RAM-floor trips over the full epoch | yes on the CPU: full loader epoch peak 166 MB; every CPU training run with the guard: no abort (fast 4.0-4.1 GB peak private vs old 6.1-6.2 GB). On the GPU: needs the window |

The L1 1024 CPU loss match with a validation stream hit the 7 GB RAM floor (guard abort at 6.98 GB free, own private
8.36 GB; the old loader alone holds up to 9 windows x 235 MB per stream and reads ~10x ahead). The recorded pair uses
L1 256 without a validation stream; the loader output does not depend on the net width.

## Finding for Engine NNUE: `--seed` does not make npt runs reproducible (independent of the loader)
`train.py` builds the model (line ~252) before it calls `torch.manual_seed(args.seed)` (line ~278), and this torch
build (2.11.0+rocm7.13.0) seeds its default generator from the clock in every process (two fresh processes:
`torch.initial_seed()` 271615243781900 vs 271624007961800, different `torch.rand(3)`). So every npt run starts from
different initial weights whatever `--seed` says; two CPU runs with the same loader and data differed from the first
logged step. Optional fix (NOT applied anywhere): `patches/0006-seed-before-model-OPTIONAL.patch` (seed before the
model is built; the later seeding stays). Engine NNUE decides; the loss match here uses the same fix inside its own
test wrapper `tools/lm_det.py` instead of changing the trainer.

## Why "old --num-workers 1" is the reference
The live line runs `--num-workers 4` = 3 decode workers + 1 builder. Its decode workers race for chunks and each
keeps its own filter state and random engine, so its batches differ from run to run and cannot be reproduced by any
loader. With 1 or 2 workers there is one decode worker and the stream is a pure function of the file (shown above).
The fast loader gives that stream at any thread count. Statistically the w4 and w1 streams apply the same filter
rules, but the piece-count filter adapts per decode worker, so they are not the same sample (UNPROVEN either way).

## Review milestone R14B-I1-1 (13:00-13:45; one read-only reviewer sub-agent, allowed by the brief at the time)
- Reviewed: candidate commit 264549ae, DLL a4f965aa (b4), spec, wrapper, harness, trainer patch copy; against the old
  loader source (behaviour only).
- Findings and actions:
  1. MEDIUM hang when the window is much smaller than the batch (`max_live_ = 3`): CONFIRMED, fixed (windows alive =
     max(3, ceil(batch / window) + 2)); self-test (5) window 1024 < batch 5000 passes.
  2. MEDIUM equality covers one configuration (window = 64 batches exactly; no oracle for spanning batches, random /
     early skipping, non-default spline values): CONFIRMED as a coverage gap; old-vs-new config matrix and a
     spanning-batch run past a file wrap are scheduled (TODO above).
  3. MEDIUM trainer path not proven end to end (raw C API only; patch not committed; no DLL identity printed;
     validation switch untested; `--num-workers 4` = 6 threads): fixed - patch + installer committed, start-up line with
     path / sha256 / version, `--num-workers N` = N loader threads (reader + filter + N-2 builders), FastSparseBatchDataset
     is what the running loss match uses; Dataset-level tensor hashes and a loss match with validation are TODO.
  4. LOW out-of-range double -> u64 at acceptance 0: CONFIRMED (both DLLs saturate via AVX-512 today; a plain cast
     elsewhere would not), fixed with explicit saturation; self-test (6) passes; old-vs-new with pc_y1 = 0 is in the
     matrix TODO.
  5. LOW no unique-position (HLL) metrics: ACCEPTED as a documented difference (logging only); resume from an
     old-loader checkpoint now prints that its HLL state is ignored instead of dropping it silently.
  6. LOW fail-open spots: fixed - strict skip config (no silent defaults), `next_raw` after close raises, double /
     foreign `release` stops the stream with an error (self-test (7)), `compare` refuses unhashed or different-setting
     dumps, the trainer loads the module by explicit path (no `sys.path` change). Not changed: destroying a stream while
     another thread is inside `next()` (the trainer cannot do that; documented).
- After this milestone Couns ruled out further sub-agents; later reviews are structured self-reviews (NOT independent).
- Next: loss-match fast arm -> b5 equality matrix + Dataset-level check -> ABBA -> GPU_REQUEST.md.

## Review milestone R14B-I1-2 (14:30; structured self-review, NOT independent - no sub-agents after 13:45)
- Reviewed: everything changed after R14B-I1-1 (commits d870b8ab .. 1e074d1f): loader fixes (windows-alive formula,
  saturating thresholds, double-release guard), wrapper (strict skip config, closed-stream error, thread mapping,
  HLL resume warning, DLL identity), installer + patch 0005, `lm_det.py`, `lm_run.sh`, `fl_equal.py`, check scripts.
  Candidate b5 9eb29b7d (pc1 = pc2).
- Findings and actions: (1) `fl_equal.py` counted an empty line as a batch when a stream had none -> fixed, both
  zero-batch dumps re-compared as 0 / 0; (2) `lm_run.sh` was edited while a run executed it (bash resumes by byte
  offset; the shifted point hit `python -ArgLine`, which exits on the unknown option - nothing re-ran) -> every later
  run uses a private copy; (3) `lm_det.py` did not put the trainer root on sys.path (first deterministic attempt
  failed at import) -> fixed; (4) the trainer is not reproducible because it seeds after building the model ->
  documented finding + optional patch 0006, worked around in the test wrapper only; (5) TaskStop leaves
  Start-Process children running -> documented, waited for the orphan before the next CPU step.
- Checks after the fixes: self-test 7 groups local + CI ASan/UBSan/TSan (run 41446915233); all b5 equality checks
  (standard, 24-config matrix, 3,100 spanning batches, trainer path); exact CPU loss match; ABBA; full-epoch run.
- Open: the GPU-window epoch (GPU busy with the npt queue). Next action: Engine NNUE / QA decide about a window
  (GPU_REQUEST.md) and about adopting `--fast-loader` via `tools/install_fast_loader.py` on a trainer copy.
