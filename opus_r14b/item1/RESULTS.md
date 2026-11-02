# R14-B item 1 - fast npt data loader (`--fast-loader`, default off) - IN PROGRESS, UNPROVEN

Branch `opus-r14b-fast-loader` (from main). Own code; the npt loader (nnue-pytorch, GPL-3.0) was read for behaviour
only (IDEA_SOURCE.md). Nothing of the live npt line was touched: the reference DLL is a copy, the trainer copy lives
in `D:\o14b\npt`. No Elo or training-quality claim; Engine NNUE / QA decide.

## Candidate
| item | value |
|---|---|
| source | `fastloader/forge_fastloader.cpp` (sha256 in logs at commit), `fastloader/forge_fastloader.py`, spec `LOADER_SPEC.md` |
| build | `fastloader/build_fastloader.sh OUT` (MinGW g++ 15.2, `-O3 -march=znver5`, static DLL, fixed random seed, no link timestamp, no auto image base), BelowNormal on CPUs 2-3 |
| DLL | **a4f965aa075f623311c5deb3a41cfa01131320dd4adf72c617f7c0f0adb2e733** (`D:\o14b\fl\b4`), second build `D:\o14b\fl\b4pc2` byte-identical (pc1 = pc2) |
| reference | copy of the queue's DLL `F:\opus_scratch\r6\nnue-pytorch-amd\build\libtraining_data_loader.dll` -> `D:\o14b\ref\` (sha256 88c01468...939c, equal to the live file) |

## Checks
| check | result | evidence |
|---|---|---|
| reference is deterministic: old `--num-workers 1` run twice, and `--num-workers 2` (same 1 decoder + 1 builder split) | 1000 / 1000 identical batches each | logs/equality/eq_old_w1*.tsv, eq_old_w2.tsv |
| **train file, first 1,000 batches (16,384,000 positions), fast at 1 / 2 / 4 builder threads vs old w1** | **1000 / 1000 identical (sha256 of the float block and the int block of every batch, plus size and active counts)** | logs/equality/b4_fast_t*.tsv |
| validation file, 300 batches, cyclic (wraps three times; 1,664,366 kept per pass) | 300 / 300 identical | val_old_cyc.tsv, b4_val_cyc.tsv |
| validation file, finite stream to end of file (partial last window, last batch 9,582 positions) | 102 / 102 identical; read 16,388,575 / kept 1,664,366 in both | val_old_fin.tsv, b4_val_fin.tsv |
| peak working set in these runs | old 769 MB, fast 165-178 MB | TSV `#` lines |
| speed seen in the equality runs (with sha256 hashing in the loop, not a benchmark) | old w1 406k kept positions/s, fast 3.42-3.44M | TSV `#` lines; the official ABBA is the next step |
| 1-epoch loss match (CPU) | TODO | - |
| speed ABBA (>= 10 pairs, CPUs 2-3, BelowNormal) | TODO | - |
| sanitizer self-test (ASan + UBSan, CI) | TODO | - |
| review milestone | TODO (after the loss match, before the bench) | - |
| GPU window epoch | TODO (GPU_REQUEST.md) | - |

Data: train `F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack`, validation
`F:\forge_j1_data\forge_holdout_013-014_j2.binpack` (read only). Settings = the npt line (`--no-filtered
--no-wld-filtered`, other skip defaults), feature set K32H3, batch 16384, window 1,048,576.

## Why "old --num-workers 1" is the reference
The live line runs `--num-workers 4` = 3 decode workers + 1 builder. Its decode workers race for chunks and each
keeps its own filter state and random engine, so its batches differ from run to run and cannot be reproduced by any
loader. With 1 or 2 workers there is one decode worker and the stream is a pure function of the file (shown above).
The fast loader gives that stream at any thread count. Statistically the w4 and w1 streams apply the same filter
rules, but the piece-count filter adapts per decode worker, so they are not the same sample (UNPROVEN either way).

## Next
CPU loss match (trainer copy + patch 0005) -> speed ABBA -> sanitizer CI -> review -> GPU_REQUEST.md.
