# R14-B item 1 - fast npt data loader (`--fast-loader`, default off) - DONE except the GPU window (requested), UNPROVEN

Branch `opus-r14b-fast-loader` (from main). Own code; the npt loader (nnue-pytorch, GPL-3.0) was read for behaviour
only (IDEA_SOURCE.md). Nothing of the live npt line was touched: the reference DLL is a copy, the trainer copy lives
in `D:\o14b\npt` (its loader files are the superseded b4 - see HANDOFF.md). No Elo or training-quality claim; Engine
NNUE / QA decide.

**State (2026-11-02 21:51 PC clock; details in the dated sections below, the newest at the end):** candidate b5
(9eb29b7d...) unchanged since 13:39. From a fresh clone with this PC's default git settings: DLL rebuilt = b5,
acceptance 261 / 261, adoption rehearsal on a fresh copy of the live trainer (264 / 264 = installer base) 261 / 261
(20:42 and again 21:48). Speed (ADVISORY): 8.65x (old w2 vs 1 builder), 6.25x in the live thread setting on CPUs 2-3,
7.19x on one logical CPU (2.45 vs 0.34 CPU-us per kept position). Damaged files: 371 fuzz runs, no crash / hang. The
live line's GPU use with the default loader: mean 45.7 % (15:14-21:14). Open: the GPU window (GPU_REQUEST.md).
`FILES.txt` + `SHA256SUMS` index this folder (`sha256sum -c --quiet SHA256SUMS` after a checkout).

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

## What the trainer gets: live layout (old loader, --num-workers 4) vs fast loader, as distributions (18:23-18:25)
`tools/fl_distribution.py stats` on the J1 training binpack, 2,000 batches of 16,384 = 32,768,000 positions each
(about 1.1 passes over the file), CPUs 2-3 BelowNormal; old = reference DLL copy `D:\o14b\ref` with 4 workers (the live
layout: three decode workers with their own filter states, not reproducible), fast = b5 with 1 builder (= the old w1
stream). `compare` (logs/distribution/compare.txt, the two JSON files beside it):
| histogram | total-variation distance | chi-square (dof) |
|---|---|---|
| piece count (0-32) | 0.00048 | 25.3 (29) |
| side to move | 0.00027 | 4.8 (1) |
| outcome (0 / 0.5 / 1) | 0.00007 | 0.4 (2) |
| queen bucket | 0.00013 | 5.2 (3) |
| score, 100-cp bins | 0.00057 | 57.2 (60) |

Mean score 0.08 vs 0.21 (internal units): difference -1.17 standard errors (batch-to-batch spread). Every distance is
below 0.001: switching the live line from w4 to the fast loader changes the sample, not the distribution (chi-square
values treat positions as independent, which positions inside one shuffle window are not, so they overstate any
difference).

## Acceptance check for Engine NNUE (18:45-18:46): `tools/fl_acceptance.sh`
- One command on a switched trainer copy, CPU only with the GPU hidden: the trainer's own Dataset ->
  FixedNumBatchesDataset -> DataLoader path, old loader w1 vs fast loader w4, every tensor of 200 training and 61
  validation batches hashed and compared. On `D:\o14b\npt`: old 36 s, fast 6 s, **261 / 261 batches identical**
  (logs/acceptance/). The script locates itself before changing directory and refuses a copy without the switch.

## Bug hunt #1 (19:05-19:12, a short first pass; self-review, NOT independent)
- `tools/fl_abba.py` used Student t only for exactly 10 pairs (1.96 otherwise: a too narrow CI for fewer pairs; the
  recorded 8.65x used 10 pairs, so its CI 8.58-8.69 stands): now a t table for 1-30 degrees of freedom, checked
  against scipy.stats.t.ppf(0.975) (0 mismatches). `tools/b5_checks.sh`: tools folder overridable (`FL_TOOLS`).
- (19:20) A fresh clone on grok-pc (git's global `core.autocrlf=true`) would check `forge_fastloader.py` out with CRLF,
  so its sha256 would not be the 39af47b0... that HANDOFF.md names: `opus_r14b/.gitattributes` now keeps code,
  scripts and docs LF in every checkout (logs byte-exact). A rebuild of the DLL from a fresh clone follows (it must
  give 9eb29b7d... again).
- (19:27, works in Forge) The DLL needs no MinGW runtime: `objdump -p` lists only KERNEL32.dll and the Windows UCRT
  API sets (api-ms-win-crt-*), and Python loads it and reads its version with PATH = `C:\WINDOWS\system32;C:\WINDOWS`
  only (the trainer started by the queue does not have MSYS2 / Git folders on its PATH).

## Bug hunt #2 (19:41-19:47 by the PC clock; self-review, NOT independent)
- H2-3 installer: the validation pass of `--loader-dll` printed "would copy" in a real install -> silent unless
  --check. Check / install / second install on fresh copies of the live config.py + train.py: OK / patched + copied
  (9eb29b7d..., 39af47b0...) / exit 2; the fresh install equals the tested trainer copy byte for byte.
- H2-5 (documented, not changed): the filter walks a chunk in 34-byte records and would ignore a damaged chunk's tail
  that is not a whole record instead of reporting it. Changing it means a new DLL and re-running every equality check
  of b5, for a case that valid files cannot produce: a read-only header scan shows every chunk of both J1 binpacks is
  whole records (train 9,915 chunks / 304,999,573 records, holdout 533 / 16,388,575 - the known counts). Noted in
  HANDOFF.md's scope; a future loader version should report it.
- The queue's wrapper `guard_exec.py` puts the script's own folder first on sys.path before runpy: a trainer copy at
  any path imports its own modules and the installed forge_fastloader.py. The copy's opus_tools\guard_exec.py has the
  adapter's pinned md5 0a794fbe..., so the GPU_REQUEST command works as written.

## Bug hunt #3 (20:07-20:09 by the PC clock for item 1; self-review, NOT independent)
- Trainer path: does the trainer copy a batch out of the fast loader's ring buffer before
  `FastSparseBatchProvider.__next__` releases it? Yes: the live tree's `data_loader/_transport.py::_pin_and_move`
  always makes a new tensor (`torch.empty` + `copy_` / memmove; pinned or not, also for device "cpu"), and the
  packed-index path that would read the batch differently needs `native_owned` + CUDA without HIP, which the ROCm
  trainer never takes. The int block is read as ONE array from `batch.white` (white | black | piece_count |
  queen_bucket), which the DLL allocates contiguously (checked by every batch-equality test). No use-after-release.
- DLL shutdown / error paths re-read (destructor sets stop, wakes all five condition variables, joins reader, filter
  and builders; `next()` returns null on stop or error and the Python side raises the error text; a release of a
  batch that is not handed out stops the stream with an error): no finding. Code unchanged (b5 9eb29b7d).

## After hunt #3: launcher fix (20:24-20:27; the same file on all three R14-B branches)
`tools/lowrun.ps1` ended with exit 0 when Start-Process could not start the program (missing file) and ran it with an
invalid handle when a redirect folder did not exist. Now exit 127 with a message for a missing program, a missing
stdout / stderr folder or a missing stdin file; the program's own exit code otherwise (sha256 cc7f28dd..., checked:
127 / 127 / 127 / 127 for the four failure cases, 3 for `cmd /c exit 3`, 0 with the expected output for a redirected
echo and a stdin redirect). Item 1's callers (build_fastloader.sh, fl_acceptance.sh, lm_run.sh, b5_checks.sh) also
check their outputs (DLL sha256, batch hashes), so no recorded result was affected.

## Verify chain 20:29-20:39 (`opus_r14b/checks/verify_chain.sh 2030` on opus-r14b-status; logs/chain_2030/)
- Fresh clone of this branch (ffa0fedc, git's default core.autocrlf=true): DLL rebuilt = **9eb29b7d** (b5),
  forge_fastloader.py 39af47b0; acceptance with the rebuilt DLL on D:\o14b\npt: **261 / 261 batches identical**.
- Loader ABBA in the live thread setting (old `--num-workers 4` vs fast with 2 builders = `--num-workers 4`), both on
  CPUs 2-3 (one physical core) at BelowNormal, 10 pairs of 420 batches (20 warm-up), the J1 binpack: old median
  772,284 vs fast 4,818,564 kept positions / s, per pair B/A 5.98-7.08, **median 6.25x, mean 6.37x, 95% CI 6.13-6.60**
  (ADVISORY; the first old run, 666,849, was the slowest - cold start). The 8.65x of R14B-I1 compared old w2 with fast
  1 builder (each 3 threads). A 1-second robocopy test of mine (27 MB to C:) ran at about 20:35, i.e. during one of the middle pairs (the log has
  no per-run times; ~6 s per run); no pair falls outside the 5.98-7.08 spread.
- Adoption rehearsal: failed for a reason outside the loader (Git Bash turned robocopy's `/E` into `E:/`, nothing was
  copied); fixed (MSYS_NO_PATHCONV) and re-run from a new fresh clone - see the next entry.

## Fresh-clone checks again after the robocopy fix (20:39-20:42; logs/chain_2030/fresh_checkout_rerun_2039.log): 0 failures
- Clone of this branch at 1a97de6b: DLL rebuilt = 9eb29b7d (b5), forge_fastloader.py 39af47b0, Windows self-test
  (MinGW -O2) ALL PASSED, acceptance with the rebuilt DLL 261 / 261.
- **Adoption rehearsal (HANDOFF steps 1-3b) PASS**: a fresh robocopy of the live trainer tree
  (`F:\opus_scratch\r6\nnue-pytorch-amd`, 382 files) matched the installer's base manifest at 20:41 (264 / 264);
  `install_fast_loader.py <copy> --loader-dll <rebuilt DLL>`: anchors OK, config.py patched (CRLF kept), train.py
  patched (LF), DLL and forge_fastloader.py copied next to train.py (sha256 9eb29b7d... / 39af47b0...); then
  `fl_acceptance.sh <copy> <out>` with its defaults (the copy's own old DLL, the installed fast files): old w1 25 s,
  fast w4 6 s, **261 / 261 batches identical**.

## Bug hunt #4 (20:50-20:56 and 21:04-21:12 by the PC clock, between them Couns's two messages; self-review, NOT independent): damaged binpack files (`tools/fl_fuzz.py`)
Scope: can a damaged or unusual binpack crash or hang the fast loader? New tool `tools/fl_fuzz.py` cuts the first 3
chunks of the J1 holdout binpack (3,145,782 bytes, read-only), writes seeded damaged copies and runs each through
`fl_equal.py dump --loader fast` in its own process (base interpreter, so a timeout ends the real process; BelowNormal,
CPUs 2-3): empty file, short header, header only, wrong magic in chunk 1 / 2, chunk size 0 / below one record / with a
partial record tail / over 100 MiB / past the end, a cut at a chunk boundary, a duplicated chunk, 10 random
truncations, random byte flips (1, 4 or 32 per file) and a file whose every score is VALUE_NONE.
| run | result |
|---|---|
| b5 DLL, 45 runs (20 flips, seed 20261102) | 0 unexpected: every header / size / truncation case a clean `fast loader: ...` error, the valid cuts load |
| b5 DLL, 326 runs (300 flips, seed 7) | **0 crash, 0 hang**: 177 load, 149 clean errors (104 chained-record flag, 23 more than 32 pieces, 12 truncated chunk, 3 record without both kings, ...) |
| the same 326 cases on a `-D_GLIBCXX_ASSERTIONS -UNDEBUG` build (scratch, sha256 572c232a...) | 0 assertion failures, 0 crash, 0 hang; 325 / 326 outcomes identical to b5 (next row) |
| H4-1: flip_238 loads 4 batches on b5 but errors on the assertions build | not a data difference: with 100 batches requested both builds fail with "record without both kings" in all 3 runs each. A builder working ahead stops the whole stream the moment it meets a bad record (fail fast), so whether earlier batches were already handed out depends on thread timing. No batch with a bad record is ever handed out. Documented, no change |
| H4-2: every score VALUE_NONE (the skip filter keeps nothing) | finite: 0 batches (old loader: 0 batches). **Cyclic: waits forever - the old loader does exactly the same** (both checked with a 20-s limit, 20:51; children ended, no leftovers). A property of the design shared with the default loader, impossible with the J1 data (~10 % kept per pass). Documented in HANDOFF.md's scope; a later version could raise an error after many whole passes without a kept position (b5 stays unchanged: it is the verified candidate) |

Logs: logs/fuzz/. The fuzz cases are part of `tools/fl_fuzz.py` (the VALUE_NONE file in finite mode only).

## The GPU use the fast loader is meant to raise: a measured baseline (21:14; read-only)
`opus_r14b/tools/gpu_util_stats.py` (branch opus-r14b-status) on the HWiNFO log the crew's npt keeper reads (one sample
every ~2 s), while the live npt line ran with the default loader (`--num-workers 4`):
| window (2026-11-02, PC clock) | samples | GPU Utilization mean / p50 / p90 | >= 90 % | <= 10 % | Compute 0 usage mean | PPT mean |
|---|---|---|---|---|---|---|
| 15:14-21:14 (6 h) | 10,790 | **45.7 % / 48 % / 78 %** | **4.0 %** of samples | 13.5 % | 44.4 % | 104.2 W |
| 12:00-21:00 (9 h) | 16,184 | 46.0 % / 48 % / 78 % | 3.8 % | 11.7 % | 44.9 % | 104.6 W |

Hourly means 15:00-21:00: 53 / 43 / 40 / 42 / 56 / 43 / 40 %. This is the "GPU at 25-50 %" of the brief, measured. It
does not by itself show that the loader is the cause (validation, checkpoints and the 2 s sampling are in it): the GPU
window measures the same column with `--fast-loader` (GPU_REQUEST.md, same command) - item 1's target is >= 90 %.

## How much CPU the live trainer gets (21:19-21:32; read-only measurements; the "starved" wording of 21:20 corrected)
- The old loader alone, on 2 free logical CPUs in the live thread setting, makes 772k kept positions / s (verify chain
  ABBA) - 4.6-6.4x what the live line consumes (7.4-10.3 it/s x 16,384 = 121k-169k / s). So on a free core it is not
  the limit; the question is how much CPU it gets in the live run.
- At 21:19:47 the npt trainer process (Idle, mask 0x3 = CPUs 0-1, 28 threads: loader workers + the training loop) got
  **0.57 cores over 10 s** - a quarter of its two CPUs - while two crew jobs at BelowNormal with affinity on all CPUs
  (Astra's `audit_forge_admission.py`, pids 8624 / 6376) used ~1.0 core each; BelowNormal always runs before Idle.
  GPU Utilization over the same minutes: mean 50 % (HWiNFO, 90 samples).
- Per-CPU busy time at 21:32 (Windows counters, 5 samples of 2 s): CPU 0 90.5 %, CPU 1 85.7 % (the trainer's two),
  CPU 2 67.6 %, CPU 3 82.7 %, the whole PC 93.4 %. So the trainer's CPUs were mostly busy with others' work, yet 10-14 %
  of their time was still idle - time an Idle-class process can take. **The trainer is therefore not purely CPU-starved
  at that moment**: part of its waiting is elsewhere (GPU, I/O). The heading of 21:20 ("starved") said more than the
  data shows; corrected in hunt #5 (21:32).
- Reading: the trainer's data path shares its CPUs with heavier-class work; a loader that needs ~7x less CPU per kept
  position (next entry) leaves more of the trainer's share for the training loop. Whether that raises the GPU use, and
  by how much, only the GPU window can show. Whether to keep BelowNormal crew jobs off the trainer's CPUs, or give the
  trainer another class, is the crew's call (FINAL_REPORT owner items); nothing was changed. The overnight watcher
  (C:\o14b\trainer_watch_night.tsv) logs the trainer's share and the GPU use every 5 min; its "others" column counts
  processes ALLOWED on the trainer's CPUs (their CPU time may come from other CPUs), the trainer's own share is exact.

## CPU cost per position: both loaders on ONE logical CPU, live thread setting (21:23-21:27; logs/abba_1cpu/)
`fl_abba.py --pairs 10 --mask 0x4 --priority BelowNormal`, old `--num-workers 4` vs fast with 2 builders, 420 batches
per run (20 warm-up), the J1 training binpack; load before: two crew BelowNormal jobs on all CPUs (~1 core each).
| | kept positions / s (median) | CPU-us per kept position | CPU to feed the live line (121k-169k / s) |
|---|---|---|---|
| old loader (live layout) | 407,670 | 2.45 | **0.30-0.41 of a CPU** |
| fast loader | 2,909,398 | 0.34 | **0.04-0.06 of a CPU** |

Per pair B/A 6.91-7.38, **median 7.19x, 95% CI 7.08-7.26** (ADVISORY). With the 0.4-0.6 cores the trainer process got
at 21:19-21:22, the old loader alone needs most of that share to keep up, leaving little for the training loop
(tensor copies, kernel launches); the fast loader needs about a tenth of it. This is CPU arithmetic, not a GPU
measurement: the GPU window decides (GPU_REQUEST.md).

## Bug hunt #5, item 1 part (21:40-21:44; self-review, NOT independent)
| # | finding | fix | check |
|---|---|---|---|
| H5-6 | `tools/fl_acceptance.sh` passed the tools folder and the output folder unquoted inside lowrun's argument line: a path with a space (a checkout under `C:\Users\Some One\`) would split there | both paths quoted | acceptance into "C:\o14b\acc space test b5 2143": 261 / 261 |
| H5-7 | since 19:24 the acceptance check takes the loader files next to the copy's train.py by default; `D:\o14b\npt` - the copy HANDOFF.md names - holds the superseded **b4** files (12:43), so the documented command on it now failed with an obscure AttributeError. Not a mix-up of evidence: the 18:46 run used the then-default b5 folder and its log names the b5 DLL (9eb29b7d...) | the check prints a note when the fast DLL is not b5; fl_dataset_equal.py stops with "forge_fastloader.py predates the b5 candidate" for a b4-era file; HANDOFF.md says what `D:\o14b\npt` holds and how to pass the b5 folder | stale copy: note + clear message (exit 1); b5 folder given: 261 / 261 |

After H5-6 / H5-7: fresh-clone checks again (21:44-21:48, clones a64dd643 / 2a2a68dd): 0 failures - suite 150 / 0,
probe builds = the tested exes (500 / 500 reference answers), DLL rebuilt = b5, acceptance 261 / 261, adoption
rehearsal on a fresh live-trainer copy (264 / 264 = installer base) 261 / 261 (C:\o14b\vc_2144).

## Bug hunt #6, item 1 part (22:17-22:27; self-review, NOT independent): the installer's arguments and inputs
| # | finding | fix | check |
|---|---|---|---|
| H6-1 | `tools/install_fast_loader.py` ignored arguments it did not know: a misspelt `--chek` turned "only check" into a real install (exit 0, config.py + train.py of the copy patched) | arguments are parsed strictly: anything but `--check` and `--loader-dll PATH` is exit 2 with the usage text, before any file is read | `misspelt_check` + `misspelt_check_changed_nothing` |
| H6-2 | a folder without config.py / train.py, or a train.py that is not UTF-8, ended in a Python traceback (exit 1) | exit 2 naming the file ("cannot read it as a trainer file") | `no_folder`, `not_utf8` (+ config.py untouched) |
| H6-3 | the docstring said "never run it on the live trainer folder" but nothing stopped a real install into `F:\opus_scratch\r6\nnue-pytorch-amd` | a real install there is exit 2 ("install into a COPY", HANDOFF.md step 1); `--check` (read-only) stays allowed | `live_install_refused`, `live_check_allowed`, `live_unchanged` (the live files' sha256 before = after) |
| H6-4 (advisor read, 22:29) | my own first `test_installer.sh` checked H6-3 by sending a real install command to the real live folder and relying on the new guard to refuse it: a regressed guard would have patched the live trainer. It ran twice that way (22:25, 22:26): refused both times, live files unchanged (sha256 before = after, and at 22:34 still = the installer's base manifest: config.py 4d743883..., train.py bed2d764...) | the guard is now tested on a copy of the installer whose `LIVE_TRAINER` names a stand-in folder (fresh copies of the two files); a text check that the committed installer names the live folder; only the read-only `--check` goes to the real folder | 25 / 25 PASS (logs/installer/test_installer_v2.log); with a planted installer whose guard is removed, the two guard cases FAIL and the install lands in the stand-in only (logs/installer/test_installer_planted_guard_removed.log) |

`tools/test_installer.sh SCRATCH [LIVE]` (new; copies of the live config.py + train.py, the live folder only read; first version, before H6-4):
**22 / 22 PASS** on the fixed installer (logs/installer/test_installer_new.log, per-case outputs next to it). The same
script against the previous installer (edcdcd0d), with a copy standing in for the live folder: 9 FAIL - H6-1 (and two
cases that fail after it because the copy was already patched), H6-2 twice, H6-3 twice, and one text-only difference
(the old "--loader-dll needs a path" was already exit 2) (logs/installer/test_installer_on_previous_installer.log).
The patching itself is unchanged: config.py / train.py installed by the fixed installer are byte-identical to those
of the 21:44 adoption rehearsal (sha256 5c41d7a7... / d9c3ccef...), which passed acceptance 261 / 261.

Fresh-clone checks again after H6-1..H6-4 (`fresh_checkout_checks.sh`, 22:35-22:39, clones 2c689948 / 886ae6f5 with
this PC's default git settings): **0 failures** - relabel suite 155 / 0, probe builds = the tested exes (500 / 500
reference answers), DLL rebuilt = b5 (9eb29b7d...), Windows self-test ALL PASSED, acceptance 261 / 261, and the
adoption rehearsal with the fixed installer from the clone on a fresh copy of the live trainer tree (264 / 264 = the
installer's base): anchors OK, patched, DLL + forge_fastloader.py copied, acceptance 261 / 261
(logs/fresh_2235/fresh_checkout_checks.log).

## Bug hunt #7 (22:49-22:52 by the PC clock, started early; self-review, NOT independent): the fail-closed scope
Scope (written first): the fast loader claims to refuse everything outside its proven scope instead of giving batches
that differ from the old loader; the refusals were in the code (forge_fastloader.py `_check_scope`, `make_config`;
chained records in the DLL, tested by the self-test and fl_fuzz.py) but the Python ones had no test and no log.
New `tools/test_scope.py` (standard library + the DLL; no torch, no GPU runtime): **20 / 20 PASS**
(logs/scope/test_scope.log) - a feature set other than K32H3 (HalfKAv2_hm; also "K32H3^": the trainer passes
`model.input_feature_name`, which is "K32H3" for the factorized K32H3^, as the acceptance runs show), two files or none,
DDP with 2 ranks (1 rank accepted), filtered / wld_filtered / simple-eval skipping, no skip config, a skip config
without `pc_y3`, a missing binpack and a folder given as binpack ("fast loader: cannot open ..."), a missing DLL
(FileNotFoundError naming it) and, for patch 0005, a `FORGE_FAST_LOADER_DIR` without forge_fastloader.py
(FileNotFoundError naming the file); positive control: the live line's settings on 3 chunks of the J1 holdout give a
first batch of 1,024 positions. Planted check: with the DDP refusal removed from a copy of forge_fastloader.py,
`scope_ddp_two_ranks` FAILs (logs/scope/test_scope_planted_ddp_removed.log).
No finding in the code. Noted: the feature-set / file / DDP checks run when the trainer builds the dataset, the
skip-setting checks when the stream starts (the first batch of the first step), still before any batch is given out;
moving them earlier would change forge_fastloader.py (39af47b0..., pinned by the acceptance and fresh-clone checks)
for no change in what is refused, so it stays as it is.

## The queue moved to the next npt line (seen 22:54-22:59; read-only)
The watcher (C:\o14b\trainer_watch_night.tsv) shows the trainer's mask changing from 0x3 to 0xF at 22:29 and a new
trainer process at 22:34 (pid 13960 -> 11328); the keeper's STATUS names the new run
`npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s31`. Its command line (read 22:59) keeps everything the loader sees:
`F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack`, the 013-014 holdout for validation, K32H3^, L1 1024,
batch 16384, `--num-workers 4 --threads 2`, epoch 152.5M, `--no-filtered --no-wld-filtered`; only the seed differs
(5124 vs 5117) [corrected in bug hunt #11: this 22:59 text also named lr 0.000875 and gamma 0.72 as different;
they are the same as the request's command - the run names share g072 / lam10]. The trainer files are still the installer's base (264 / 264 in the 22:35
fresh-clone rehearsal), so GPU_REQUEST.md and HANDOFF.md apply to the new line unchanged (GPU_REQUEST.md notes it).
GPU_REQUEST.md's pre-checks run as written (23:02, read-only): 1 finds the live trainer (2 processes match
`nnue-pytorch-amd\train.py`, pids 8308 / 11328) -> "do not start", as it must while the npt line trains; 2 RAM free
15.3 GB, C: 131.7 GB, D: 53.5 GB -> pass; 3 the b5 DLL's sha256 9eb29b7d... and the switch in `D:\o14b\npt\train.py`
(4 lines) -> pass.
A CPU dry run of the GPU command's recipe (`tools/lm_run.sh fast` with validation, L1 1024, 4 steps, `--save-top-k
1`) was stopped by the session's permission check at 23:09 before it started ("Interfere With Workloads": a CPU
training run on CPUs 2-3, which the live trainer's mask has included since 22:29). Not worked around; nothing ran
(no output folder). GPU_REQUEST.md lists it as optional pre-check 4, for a moment when no npt line trains. The
trainer's CLI with `--fast-loader` did run in the afternoon's CPU loss match through the same launcher.

## Bug hunt #8 (23:10-23:11 by the PC clock, started early; self-review, NOT independent): the DLL's lifecycle
Scope (written first): forge_fastloader.cpp create / next / release / destroy, errors in its threads, and teardown
while the trainer waits for a batch - a race there would show at the end of training or when a stream is dropped.
Read: `Loader::~Loader` sets `stop_`, wakes every condition variable and joins the reader, filter and builder threads,
but not an outside caller still inside `next()`: destroying a stream while another thread waits in `ffl_next` would
free the mutex under it. Reachable from the trainer? No: the live trainer's `FixedNumBatchesDataset`
(`F:\opus_scratch\r6\nnue-pytorch-amd\data_loader\dataset.py`, read-only) fetches batches on one daemon prefetch thread
that holds the iterator, so our provider (and its stream) is freed only after that thread has left `ffl_next`;
`__del__` there sets a stop event and joins with a 1 s timeout. Errors raised in `ffl_next` reach the trainer through
the prefetch queue. Worker-thread exceptions are caught (`guarded`) and become the stream's error; a double or foreign
`ffl_release` stops the stream with an error (self-test case 7). No code change (a DLL change would void the b5
evidence for no reachable failure); the contract is now LOADER_SPEC.md section 7.

## Bug hunt #9 (23:19-23:20 by the PC clock, started early; self-review, NOT independent): what the trainer asks of the dataset
Scope (written first): every attribute of the training dataset the live trainer uses after the first batches - a
missing one would fail only at an epoch end, a checkpoint or a resume, which the acceptance batches do not reach.
Read (read-only, `F:\opus_scratch\r6\nnue-pytorch-amd`): `trainer/callbacks.py` calls, through
`FixedNumBatchesDataset`, `get_unique_stats()` (ours: exact preskip / total, unique 0), `get_hll_state()` at every epoch
end (ours: empty bytes -> the callback skips its unique-position merge and returns, no error) and
`set_initial_hll()` on a resume (reaches our `_NoHll`, which says once that the checkpoint's HLL state is ignored);
`get_io_stats()` (ours: an empty list). The CPU loss match ran a full epoch through these callbacks. No finding.

## Claims audit (23:21-23:24 by the PC clock; self-review, NOT independent): report numbers -> raw logs
Every key number of FINAL_REPORT.md was looked up in a committed raw log (not in prose). Item 1: the ABBA ratios are
the MEDIANS of the 10 per-pair ratios, their intervals those of the MEAN ratio - 8.65x = median 8.653 (mean 8.635,
95% CI 8.577-8.692, logs/b5checks/abba/summary.txt), 6.25x = median 6.248 (mean 6.365, CI 6.126-6.604,
logs/chain_2030/abba_live.log), 7.19x = median 7.189 (mean 7.168, CI 7.078-7.257, logs/abba_1cpu/summary.txt); the
"468,494 vs 4,035,567" of HANDOFF.md are the per-arm medians, whose quotient is 8.61, not the 8.65 printed next to
them - wording fixed in HANDOFF.md, FINAL_REPORT.md and the skill (statistic named everywhere). CPU loss match
11.4 / 40.2 min = 681.5 / 2,411.5 s and peak private 4.08 / 6.2 GB (logs/lossmatch/*guard.jsonl). The GPU baseline had
no raw log: re-run read-only from the keeper's HWiNFO CSV, it gives the cited numbers exactly - 10,789 samples
15:14-21:14, mean 45.7 %, p50 48 %, >= 90 % in 4.0 % (logs/gpu_baseline_1514_2114.txt). Item 2 (its logs): 1.075x is
the probe ABBA's MEAN (median 1.094, CI 1.0439-1.1056, logs/probe_pgo/abba_r13_vs_pgo.txt) - the report now says so;
635,344 rows/h = 999,921 rows over the 5,665.77 s of labelling summed from the 100 shard summaries (the run's own
wall-clock status: 635,313), both 78.7 h for 50M (item 2 logs/pgo_full_1M_rate.txt, new); proof md5s, rows, games
and splits are in pgo_full_1M.log / conv_full_1M.txt.

## Bug hunt #11 (00:08-00:09 by the PC clock; self-review, NOT independent)
Scope (written 23:24, before the hunt): (a) superseded statements in this folder still marked as superseded; (b)
GPU_REQUEST.md's command against the live trainer's current command line; (c) the lock exe and the four candidate
exes Couns asked to keep (20:53) still in place with their sha256 (read-only).
- (c) PASS (00:08): forge_ltopgo_x_al1s198_v23.exe fd3a5190... in forge_push\bin and in the lock folder;
  forge_ltopgo_syz_pc1.exe 150374ff..., forge_ltopgo_sfs.exe 029d58e8..., forge_ltopgo_speed2_de20653c.exe
  de20653c..., forge_data_probe.exe (PGO) 08299f9f... - file times unchanged (10-30 / 11-01 / 11-02).
- (b) Finding H11-1 (mine, documents only): the live line (pid 11328, run ..._w4_s31) differs from the request's
  command only in `--seed` (5124 vs 5117); every other argument is the same (features, L1, batch, workers, threads,
  epoch, validation set and size, lr 0.000875, gamma 0.72, lambda 1.0, both binpacks, --no-filtered
  --no-wld-filtered). My 22:59 note in GPU_REQUEST.md and in this file had also called lr and gamma different - an
  unchecked claim. Fixed in both places (the RESULTS sentence keeps a correction marker); no other document carried it.
- (a) PASS: the "starved" wording of 21:20 is corrected in its section; HANDOFF.md names the superseded b4 files in
  D:\o14b\npt as superseded; counts in HANDOFF.md and GPU_REQUEST.md are current.
