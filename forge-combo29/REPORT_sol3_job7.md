# sol3 — Job 7 loop node ceilings and wall-clock record

**Step 0 passed.** All four ordinary binaries and three Job 5 probes matched their prescribed executable SHA-256 values. net768 matched SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7` and activated on k11f with checksum `30ab43b4ba5db5f3`. [Hash check](sol3/job7/known_sha256.txt) · [Raw activation](sol3/job7/net_ready_11f.txt) · [Assigned probe hashes](REPORT_sol3_job5.md)

**Prediction grade.** k11f hit exactly 50000 on all 389 B2 and N2 positions, and 250000 on all 389 N2 positions. The B2/250000 prediction missed by one, as 388 searches hit the cap. The zero best-move and score difference prediction held in all four cells. The k11 wall-time median was 90.832290 ms versus the 91 ms forecast, an error of 0.167710 ms. Its maximum was 137.774575 ms versus 105 ms, an underestimate of 32.774575 ms. The standalone prediction was pushed at `29ed139a5ace6add782c5e8301f76bf20b5ceec6` before the workload. [Prediction](sol3/job7/prediction.txt) · [Clock readback](sol3/job7/clock_readback.txt)

### Step 1 hard-node limits and final labels

All four cells used PC20, Threads 1, Hash 16 MiB and MultiPV 1. B2 used the embedded AL1 s198 weights. N2 used the pinned synthetic standalone net768. Each cell used the 389 Job 3 FENs in order, one fresh engine process per arm, and `ucinewgame`/`isready` before each FEN. Each row stores final nodes, bestmove, and the last search-info score kind and value. I added the score and the final-node parser in the single harness diff. [Harness diff](sol3/job7/node_harness.diff) · [50,000 readback](sol3/job7/readback_50000.txt) · [250,000 readback](sol3/job7/readback_250000.txt)

| Limit | Cell | Searches per tree | k10f at limit | k11f at limit | Pf at limit | k10f/k11f rows equal | k11f/Pf final increases | Control |
| ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 50000 | B2 | 389 | 389 | 389 | 0 | yes | 389 | pass |
| 50000 | N2 | 389 | 389 | 389 | 0 | yes | 389 | pass |
| 250000 | B2 | 389 | 388 | 388 | 0 | yes | 388 | pass |
| 250000 | N2 | 389 | 389 | 389 | 0 | yes | 389 | pass |

**All four controls passed.** k10f and k11f agreed in all 1556 searches on final count, best move, and last-iteration score. Both stayed within their assigned ceiling. Pf added one node exactly when k11f reached the ceiling and matched the final count elsewhere. The one below-limit search was B2 position 165 at the 250000 budget. All three builds reached depth 64 there, finished at 220357 nodes, and returned `g1h1` with score `mate -4`. [Exact FEN and raw last lines](sol3/job7/limit_exception.txt)

### Step 2 `go movetime 100` record

I ran the ordinary k10 and k11 binaries serially with embedded AL1 s198, PC20, Threads 1, Hash 16 MiB and MultiPV 1. Each used the first 100 fixture FENs with an engine reset and ready barrier before each search. The timer used `time.monotonic_ns` from immediately before writing `go` until the OS read returned the full `bestmove` line. python-chess 1.11.2 checked each move independently against its FEN. [Timing harness](sol3/job7/clock_harness/movetime.py) · [Raw clocks and legality readback](sol3/job7/clock_readback.txt)

| Tree | Bestmove lines | Legal | Median wall time | Maximum wall time |
| --- | ---: | ---: | ---: | ---: |
| k10 | 100 | 100/100 | 90.761193 ms | 120.768226 ms |
| k11 | 100 | 100/100 | 90.832290 ms | 137.774575 ms |

## Facts

- The inherited probes use GCC 14.2.0, libstdc++ 6.0.33 and CMake Release with the Job 4 flags. The Job 5 probe prints final `SearchInfo.nodes` during the hard-node path, independently of the last completed-iteration UCI nodes. Job 7 kept those binaries byte-identical. [Source and compiled probe receipts](REPORT_sol3_job5.md) · [Retained build hashes](sol3/job7/known_sha256.txt)
- The independent checker reconstructed every row from the raw UCI output, verified the exact commands and fixture order, and checked the planted final node count for each pair. The three probe arms within a cell ran concurrently under the four-CPU cloud quota. The two clock runs ran after the fixed-node matrix and were serialized. [Independent checker](sol3/job7/compare_limits.py) · [Exact runner](sol3/job7/run_limits.sh)
- The clock summaries preserve both the driver measurements and independent medians and maxima from all samples. Complete FENs, bestmove lines and wall times per search are saved for each tree. [k10 samples](sol3/job7/clock_k10/searches.jsonl) · [k11 samples](sol3/job7/clock_k11/searches.jsonl)

## Suspicions

B2 position 165 is consistent with the depth ceiling taking effect before the 250000-node cap. Pf’s matching 220357 count there checks the plant’s behavior away from the cap. The wall record includes process dispatch and scheduling in addition to the engine clock. The recorded maximum alone does not identify where the extra delay occurred.

## What I did not do

I ran no speed comparison, external game clock, match, training or tests on the owner’s PC. The repository changes contain only text evidence, harnesses and reports on the sol3 branch.

## What I am not sure about

More than one thread, MultiPV, a game clock (wtime / btime), speed (no timing in this job), positions the fixture does not reach.

The fixed-node result establishes final-count and last-iteration label identity for this fixture. The 100 ms check records wall time under this cloud session’s scheduling conditions. [Clock and checkpoints](sol3/job7/stamps.txt)
