# seat 20 — check of seat 28's S-F1 (`go movetime M` stops at M − Move Overhead)

Verdict: **CONFIRMS seat 28's S-F1**, with my own timing harness and independent numbers.

Raw: `out_check.txt` (pasted), `check_s28f1.json` (all 75+55 runs as data). Script: `check_s28f1.py`.
Build: `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins). Machine: 4 cores.

## The result (15 runs per cell, monotonic clock, go → bestmove)

| movetime | overhead | median | p99 | max | median − requested |
|---|---|---|---|---|---|
| 10 | default | 1.72 | 2.29 | 2.30 | **−8.28** |
| 10 | 0 | 10.72 | 10.83 | 11.25 | +0.72 |
| 50 | default | 40.94 | 41.05 | 41.27 | **−9.06** |
| 50 | 0 | 51.06 | 51.17 | 51.27 | +1.06 |
| 100 | default | 90.82 | 91.10 | 91.11 | **−9.18** |
| 100 | 0 | 101.17 | 101.48 | 101.57 | +1.17 |
| 200 | default | 190.77 | 191.12 | 191.31 | **−9.23** |
| 200 | 0 | 200.78 | 201.33 | 201.34 | +0.78 |
| 500 | default | 490.80 | 491.15 | 491.41 | **−9.20** |
| 500 | 0 | 500.88 | 501.15 | 501.53 | +0.88 |

The shortfall is **constant at ≈9.2 ms** from movetime 50 to 500 — a subtraction, not a scaling — and vanishes
with `Move Overhead 0` (where the engine lands about +0.9 ms after the request, consistent with its own dispatch).

Overhead sweep on `go movetime 100`:

| Move Overhead | 0 | 5 | 10 | 25 | 50 |
|---|---|---|---|---|---|
| median wall (ms) | 100.92 | 95.88 | 90.85 | 75.78 | 50.75 |

Perfectly linear: the option is subtracted from the movetime limit exactly.

## Agreement with seat 28
Their published figures: `go movetime 10` searches ~1 ms; `go movetime 50` stops at 40.5 ms. Mine: 1.72 ms and
40.94 ms. **Agreement within 0.5 ms on both**, from an independent harness on a different cloud VM — stronger
than my prediction 5 allowed for.

## The source, quoted (src/search.cpp, in `Worker::search`)
```
const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
...
} else if (limits.movetime_ms >= 0) {
    hard_limit_ms_ = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
    soft_limit_ms_ = hard_limit_ms_;
```
The `max(1, …)` is why `go movetime 10` still searches ~1 ms instead of 0 — a good guard.

## Why it matters in play
A GUI that sends `go movetime 100` gets a 90 ms think; the 10 ms is a deliberate network/GUI-latency allowance.
That is correct behaviour for a *clocked* game and merely surprising for analysis or a fixed-time test. The real
hazard is a **measurement**: anyone comparing engines at "the same movetime" without pinning Move Overhead is
comparing 90 ms with 100 ms.

### Suspicions, not proven
- That `Move Overhead` should not be subtracted from an explicit `movetime` at all (it is documented as a latency
  allowance for clock play). That is a design question for the PC, not something I can settle by measurement.

## What I did NOT do
- I did not test `go movetime 1`, where the `max(1, …)` guard should dominate.
- I did not test the same with Threads > 1 or a big Hash (both change the dispatch cost).
- I did not test the Windows build.

## What I am NOT sure about
- Whether the +0.9 ms overshoot at overhead 0 is dispatch cost or timer granularity. I did not separate them.

## Commands that show it again
```
python3 check_s28f1.py /agent/repos/build-base/forge /tmp/o
grep -n -A3 'limits.movetime_ms >= 0' /agent/repos/base/forge-combo29/src/search.cpp
```
