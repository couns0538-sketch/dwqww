# Opus R14-B plan (Couns's 15-hour job, started 12:05 PC clock 2026-11-02; PC clock = PT + 9 h)

Two main items, finished and verified one at a time. No Elo claims (UNPROVEN everywhere). Branches:
`opus-r14b-status` (this file, STATUS.md, TOOLS.md, FINAL_REPORT.md), `opus-r14b-fast-loader` (item 1),
`opus-r14b-relabel` (item 2). Scratch `D:\o14b\` (<= 10 GB; D: had 56.4 GB free at the start, floor 50 GB).

## Item 1: fast npt data loader (`--fast-loader`, default off) - plan

### What the research found (read only)
- Live npt line (keeper STATUS 11:53): `F:\opus_scratch\r6\nnue-pytorch-amd\train.py` (b2614500 + patches 0001-0004),
  K32H3^, L1 1024, batch 16384, `--num-workers 4 --threads 2`, epoch 152.5M, `--no-filtered --no-wld-filtered`,
  data `F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` (10.37 GB, 304,999,573 records). GPU 25.5 % (5-min avg).
- The adapter `F:\forge_nnue_train\tools\train_resid_nnuepytorch_v2.py` sets `NNUE_DATA_LOADER_LIB` to
  `...\nnue-pytorch-amd\build\libtraining_data_loader.dll`, the R6 "setup" g++ build (BMI2 off) - R6's slowest build
  (0.249 MPos/s per thread vs 0.47 for the clang build, R6 LOADER_NOTES.md).
- The run reads ~10 records for every record it trains on (epoch 0: preskip 1,606,996,009, total 161,529,856): the
  piece-count skip filter rejects ~90 %.
- The J1 binpack is unchained (34 bytes per record, constant ply 40): the skip decision needs only score, ply/result
  and the piece count (popcount of the occupancy), not a decoded board.
- The old loader has no seed input: its filter state and its `mt19937_64` (default seed) are per decode thread, and
  the same engine shuffles each 2^20-entry window. With `--num-workers 1` (one decode worker, one builder, one reader)
  the stream is deterministic; with 4 workers the order depends on thread timing. "Bit-identical to the old loader" is
  therefore measured against `--num-workers 1`; the fast loader gives that same stream at any thread count.

### Design (own code; nnue-pytorch is GPL-3.0 = ideas only, named in IDEA_SOURCE.md)
1. `LOADER_SPEC.md`: the behaviour in my own words (record layout, filter, window + shuffle, batch layout).
2. `fastloader/forge_fastloader.cpp`, MinGW g++ 15.2 (the same libstdc++ as the old DLL, so `std::shuffle` gives the
   same permutation), C API returning the old SparseBatch memory layout. Pipeline: sequential reader -> one cheap filter
   pass over the record fields -> compact kept records -> shuffle of an index permutation (not 224-byte structs) ->
   parallel feature builders writing batch k into slot k (same output for any thread count).
3. Fail closed outside the proven scope (chained binpack, more than one file, filtered / wld_filtered / simple-eval
   skipping, DDP, feature sets other than K32H3[^]).
4. `fastloader/forge_fastloader.py`: drop-in dataset class; `patches/0005-fast-loader-switch.patch` adds
   `--fast-loader` to a COPY of the trainer (`D:\o14b\npt`); the live trainer, its queue and its runs are not touched.

### Checks (done = all of them)
- Old loader `--num-workers 1` twice: identical batch hashes (reference is deterministic).
- Fast loader at 1 / 2 / 4 threads vs old `--num-workers 1`: first 1,000 training batches and the 61 validation batches
  bit-identical (sha256 of every tensor).
- 1-epoch loss match on the CPU (no HIP next to the npt line): same recipe, same seed, epoch = 64 batches; identical
  losses and identical final weights.
- Speed: loader-only palindromic ABBA (>= 10 pairs) on CPUs 2-3 at BelowNormal, old `--num-workers 2` vs fast 2 threads;
  target >= 3x (advisory; Engine QA times officially). Peak RAM recorded.
- ASan + UBSan self-test in GitHub CI; local `_GLIBCXX_ASSERTIONS` build over 1,000 batches.
- `GPU_REQUEST.md` for one full epoch in a window Engine NNUE gives (GPU use, it/s, no RAM-floor trips).
- Review milestone (one reviewer sub-agent at a time as the brief allows, else structured self-review) before the
  bench and before the GPU request.

### Reused, and why
| what | from | why |
|---|---|---|
| loader behaviour, batch layout, R6 builds and equality method | `F:\opus_scratch\r6\nnue-pytorch-amd` (read only), `opus-r6-amd-nnue` LOADER_NOTES.md / dl_equal.py | the old loader is the reference the new one must equal; R6 already showed `--num-workers 1` is deterministic |
| live run facts (args, DLL, epoch counts) | keeper STATUS, npt run logs, the adapter (read only) | the speed baseline must be the DLL the queue really uses |
| unchained J1 binpack fact | skill forge-nnue-data | makes a filter pass without board decoding possible |
| load / disk gate | `opus_r13/tools/pc_gate.ps1` (copied to `opus_r14b/tools/`) | same PC rules |

## Item 2: resumable relabel - plan follows once item 1 is pushed with its checks.
