# B1. Worst-case prediction, written BEFORE any B2 measurement
kimi5 job 1, 2026-11-16 04:14 UTC. Machine: 4 vCPU, g++ 13.3.0 Release, avx512f+bmi2.
Measured speed for the prediction: bench 16 = 3,024,920 nodes in 1,440 ms -> 2.10 Mnps
Threads 1 (tests_kimi5_job1/step0_bench16.txt).

## The prediction
The clock is looked at every 1024 nodes per worker (search.cpp:1419 qsearch, 1561 search),
and `elapsed_ms()` truncates to whole milliseconds (search.cpp:1253). After the main worker
aborts, helpers (Threads > 1) finish at most their own current 1024-node interval before the
join (search.cpp:1280, 2745-2749).

Largest time a search can run PAST ITS HARD LIMIT on this machine:
- Threads 1: 1024 / 2.10e6 s = 0.49 ms (one full check interval) + < 1 ms (ms truncation)
  + ~0.05 ms (recursion unwind, bestmove formatting, flush) ≈ **at most ~1.5 ms past hard**.
- Threads 4: the same for the main worker, plus one helper interval 1024 / ~1.5 Mnps
  ≈ 0.7 ms at the join (parallel across 3 helpers) ≈ **at most ~2.2 ms past hard**.

Since in clock play hard <= T - Move Overhead = T - 10 (clock_plan.hpp:32-46), the wall
elapsed write(`go`) -> read(`bestmove`) should obey elapsed <= T - 10 + 2.2 < T for every
T >= 20. **Predicted result of every B2 line: 0 searches longer than T; the largest elapsed
at T = 20 or 50 (hard = 5 ms) <= ~7 ms; at T = 100 (hard = 20 ms) <= ~23 ms.**

## Code paths that could exceed the limit by MORE than one interval between two looks
1. The millisecond truncation of `elapsed_ms()` — up to 1 ms beyond the interval.
2. Threads > 1: the helper join adds a second interval's worth (helpers ignore the clock).
3. Nothing else found. Checked and bounded by the same 1024-node cadence: aspiration
   re-search cascades (search.cpp:2413-2437), MultiPV alternate-line searches
   (2473-2515, their stop goes through the parent worker's clock at 1296->1265), quiescence
   capture chains (1419), the emergency 1-ply/2000-node path (2310-2320, ~1 ms at this NPS).
   Non-interruptible setup (A4) is microseconds and inside the budget, so it shifts work
   earlier but cannot push the end past hard + one interval.

If the measurement beats these bounds by more than ~2x, the model is wrong somewhere and the
first place to look is a code path that skips the 1024-node cadence.
