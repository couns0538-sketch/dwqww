# opus_finny_cache — BENCH (measurement behind the D3 gate)

All numbers below were **executed** on 2026-11-09, between 19:03 and 19:07 Vienna (PC clock 17:03-17:06). The run used CPUs 12-15 at Idle on a shared PC. No timing claim is made: only counts are used.

## What was measured
An instrumented **scratch** copy of parent P counts calls; nothing else changes. `refresh_count_scratch_after_w6.patch` holds the diff (25 added lines, measurement only, never a candidate). The scratch copy is made by `tools/rc_make.ps1`, whose anchored edits must each match exactly once. The counters:
- `nnue::refresh` calls in total, split into root refreshes (`Worker::search` start) and in-tree refreshes (`Worker::static_evaluate` fallback);
- `nnue::update` (lazy incremental update) calls;
- `nnue::evaluate` calls;
- a histogram of the walk-back length per lazy update (back = 0..8, 9+);
- a UCI command `rcdump` that prints the counters.

| item | value |
|---|---|
| scratch exe | `D:\forge_jobs_20261107\opus2\out\scratch\rc\rc.exe` sha256 `5f8b059f0acfd7b20f8f43a13cbfac4f6c4d6a7e86e0deefebb3a970c6ad2934` (plain lock line: g++ 15.2.0 `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread`) |
| FEN set | `opus_speed/data/fens_12k_v2.txt` (opus-speed-20261105), md5 `e7dbf2c8151188c03ef52054557a531e` |
| driver | `tools/rc_measure.ps1` (PS 5.1, o2_uci_lib), OwnBook false |
| raw log | `logs/refresh_count/rc_summary.txt` |

## Result
| run | searches | refresh total | root | **in-tree** | lazy updates | evals | walk-back histogram (back = 0,1,2,…,8,9+) |
|---|---|---|---|---|---|---|---|
| `bench 16` (3,024,920 nodes = pin) | 8 bench positions | 8 | 8 | **0** | 2,206,470 | 1,803,616 | 1541246 159109 47400 19064 12083 5172 2687 1177 470 427 |
| `go depth 13`, first 300 FENs, Threads 1, ucinewgame each | 300 | 300 | 300 | **0** | 27,250,750 | 21,462,454 | 17650079 2303695 687123 287108 158216 76234 35046 18740 7319 6791 |
| `go movetime 500`, 20 FENs, Threads 4 | 20 | 80 | 80 (20 × 4 workers) | **0** | 48,937,100 | 40,250,297 | 34433039 3297268 1049063 428282 270522 120256 65396 29098 14013 13944 |

### Reading
- Refreshes equal searches × workers in every run, and **no refresh happens inside the tree**.
- Refresh work compared with incremental work: in the depth-13 run, 300 refreshes of about 32 piece columns each (about 9,600 column adds per perspective) against 27.25 M updates of 2-4 column changes each (about 55-110 M column adds). That puts refreshes at roughly 0.01-0.02 % of accumulator work.
- A Finny cache could replace only that share, and only partly, since a diff against a cached board still costs a few columns.
- The walk-back histogram shows that 81-86 % of lazy updates replay a single ply (back = 0). Long chains are rare (back ≥ 9: 0.02-0.03 %), and they are incremental too: a refresh cache does not touch them.

## Not measured, deliberately
NPS with and without a cache. There is no cache to time, and the expected effect is far below the noise of any NPS measurement on this PC.
