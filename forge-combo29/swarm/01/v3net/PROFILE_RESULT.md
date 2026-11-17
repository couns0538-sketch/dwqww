# Step 1 result — the profile, scored against the prediction committed before it

Prediction: `PREDICTION.md`, commit `79eb23c98`, written and committed **before** any sample was taken and not
edited since. This file is the scoring.

Build: `227aae56ef1678…`, PC r15 + `-DFORGE_NNUE_V3=1` + `-DFORGE_MATE_ALPHA_GUARD=1`, g++ 13.3.0, generic
x86-64, AVX-512 kernel. Workload: PC20 + the test net, `Threads 1`, `Hash 16`, `bench 13` = **3,652,372 nodes**,
the same number Step 0 validated.

## The v3 path is 19.05 % of `bench 13`

43,000 samples (`task-clock` at 3,999 Hz, five `bench 13` runs in one process). Five runs took
2,168 / 2,166 / 2,161 / 2,163 / 2,161 ms, so the workload is stable to ±0.3 % and the shares below are not noise.

| v3 function | % of `bench 13` |
|---|---|
| `apply_changes_pair` (incremental update, both perspectives) | **7.41** |
| `refresh_from_pieces` (rebuild from the per-worker cache) | **4.79** |
| `evaluate` (forward pass: `output_sum_avx512` + `finish`) | **4.62** |
| `apply_changes` | 0.83 |
| `king_key` | 0.67 |
| `prepare` | 0.43 |
| `load`, `loaded`, `pieces_of` | 0.30 |
| **all v3 together** | **19.05** |

For contrast, the search around it: `MovePicker::pick_best` 10.08, `Worker::search` 8.28, `Worker::qsearch` 6.59,
`MovePicker::generate_evasions` 6.52, `MovePicker::next` 6.33, `see_ge` 4.95, `corrected_eval` 4.77.

## Scoring

| | claim | measured | verdict |
|---|---|---|---|
| **P1** | accumulator update **40–65 %** of v3, and the hottest v3 item | **68.4 %** of v3 (7.41 + 4.79 + 0.83 of 19.05); `apply_changes_pair` is the top single v3 item | **direction right, item right, magnitude 3 points above my range** — recorded as outside rather than rounded into place |
| **P2** | forward pass **10–25 %** of v3 | **24.3 %** of v3 (4.62 / 19.05) | **PASS**, at the top of my own range |
| **P3** | all v3 **15–40 %** of `bench 13` | **19.05 %** | **PASS** |
| **P4** | update is **memory-bound** on `w1`'s 6.00 MiB, not instruction-bound | **not tested** | **INCONCLUSIVE** — see below |

Kill conditions: **K1 did not fire** (update not under 20 %, and it is the top item), **K2 did not fire** (forward
pass not over 40 %), **K3 did not fire**. **K4 could not be run.**

## Why P4 is inconclusive rather than confirmed

My K4 test was "profile a net small enough to sit in L2 and see whether the update's share collapses". I cannot run
it: the FORGENN3 format fixes `hidden` at 512, so there is no small net to build without patching the loader — and a
patched loader measures my patch, not the PC's path.

The obvious substitute also failed: **the hardware PMU is not available in this VM.** `perf stat` on
`cycles`, `instructions`, `L1-dcache-loads/misses`, `LLC-loads/misses` and `cache-misses` all return
`<not supported>`; only `task-clock` works. So I have no cache-miss evidence at all, and a 6.00 MiB footprint that
*should* miss L2 is not the same as one measured to.

**What I will claim:** the accumulator update is 68 % of v3 time and `refresh_from_pieces` alone is 4.79 % of the
whole benchmark. **What I will not claim:** that the cost is misses on `w1`. That stays a hypothesis and Step 2
should not be built on it.

## The one lead the profile hands over, cheaply

`refresh_from_pieces` at **4.79 %** is almost as expensive as the incremental update it backs up (7.41 %), and
reading `nnue_v3.cpp:689` says why: it is a **full rebuild of one perspective's accumulator from a cached entry**,
costing up to ~32 column add/subs of 1 KB each, and it fires whenever a **king bucket changes** — which happens on
every king move and on every capture near the king. A king move is common; a full 512-wide rebuild per king move is
the kind of cost that a cache keyed on `(perspective, king bucket)` is meant to avoid, and it is already there —
what is missing is evidence about how often it fires versus how often it could have been an incremental update.

That is a **question for Step 2, not a speed claim**, and it needs a counter (refreshes vs columns). And here the
source answers a question I was about to build a harness for:

**`RefreshCache::refreshes` and `RefreshCache::columns` exist, are incremented, and are never read.** The header
comments them `// statistics (tests)` (`include/forge/nnue_v3.hpp:137`), but a whole-tree search finds no reader:
`src/nnue_v3.cpp` resets both at `:644–645` and increments them at `:694` and `:702/:707`, and **nothing anywhere
reads either one** — no test, no UCI output, no diagnostic. So the data Step 2 needs to size the refresh/update
split is already being collected and thrown away.

That is cheap to fix and worth fixing before any Step 2 patch: **one `info string` line per search reporting
refreshes and columns turns a guess about how often the cache path fires into a measured ratio**, with no change to
search behaviour and no risk to the identity numbers. It is also the honest order of work — the counter comes
first, so the patch is aimed at a measured cost rather than at a plausible one.

This is a `v3` finding about **instrumentation**, not a speed result: I have not measured the ratio, only
established that the engine already counts it and discards it.

## Method note that matters to the next seat

`gprofng` produced a **complete-looking profile from 22 samples** — 0.022 s of CPU attributed out of a 2.2 s run, at
`-p high` — and reported success. It did not follow the engine child, and the tables it printed had plausible
percentages. That is filed as **Trap 10** in `../MEASUREMENT_TRAPS.md`: a profiler's output is a measurement, so it
needs a sample count before it means anything. The sample count is the first number to read, not the percentages.
