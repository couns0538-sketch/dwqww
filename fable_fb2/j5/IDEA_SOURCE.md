# IDEA_SOURCE — FB2-J5 (Lazy SMP v2)

## Analysis of the R3-6 data (`opus_r3/R3-6/REPORT.md`, `R3-6Q`)
- Stack OFF scaled 0.95x (Threads 2) and 1.14x (Threads 3) in suite time-to-depth, with node inflation 1.71x / 2.03x
  and NPS scaling 1.86x / 2.43x: the extra threads produced nodes but barely shortened the main thread's critical
  path (main nodes 0.80x of Threads 1 at T2, 0.68x at T3; TT hit rate 33% -> 35%).
- Trace: helpers duplicated the main thread (same depth sequence, in lockstep, "lead" of only 0.5-0.6 ply), so most of
  their work re-searched subtrees the main thread was about to search itself; openings (largest trees) scaled worst
  (0.92x at T2, i.e. slower than one thread).
- R3-6's own fix (helpers past the depth limit) removed idle time but gave no time-to-depth gain (R3-6Q quiet runners:
  1.10 / 1.02), because the helpers still searched the same depths as the main thread.
- The R3 "on" set (SmpExactNodes + SmpBestThread + LocklessTT) gave 1.28x per-position at T2 on the PC but was not
  significant; LocklessTT costs 2.2% at Threads 1 on Linux.

Conclusion: the justified fix is **helper diversification**, not more helper time: helpers must search different
depths / windows so that their TT entries are useful when the main thread arrives, plus reporting the deepest
completed result. Shared-TT contention (a lockless table) is the second-order issue and stays out (it is S13 /
LocklessTT on the R3 stack).

## Ideas used
| element | source (idea only) | here |
|---|---|---|
| helpers search different iteration depths ("skip iterations" / depth offsets) so that half the threads are one ply ahead | Stockfish 2016-2019 Lazy SMP (`skipSize` / `skipPhase` tables, later `rootDepth += ...`), Ethereal / Berserk (helper depth offsets) | odd helpers search depth + 1 (`fb2::smp_depth_skew`) |
| diversified aspiration windows per helper | own variation of the same principle (different windows produce different trees and fail-high/low paths) | even helpers use 2x / 3x / 1x the aspiration delta (`fb2::smp_aspiration_multiplier`) |
| report the deepest completed result among threads | Stockfish's best-thread selection (depth/score vote), R3 SmpBestThread (not merged into this base) | `fb2::smp_select_result`: deepest completed search with a best move; ties keep the main thread; node/time totals stay the main's |
| per-thread histories and correction tables | already per worker in the lock; unchanged | - |
| measurement method (fixed-depth suite, fresh process per run, paired ratios, node inflation, NPS scaling) | R3-6 (`smp_ttd.py`, `positions30.tsv`) | `tools/smp/fable_smp_ttd.py` (single file, same statistics) |
