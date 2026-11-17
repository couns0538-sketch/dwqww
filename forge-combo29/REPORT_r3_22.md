# Clock time safety

The idea comes from Finding 5 in `forge-combo29/AUDIT_lock_source.md` at commit `302a08a2` on `audit/lock-source`, and from the two clock setups in `forge-combo29/tests_audit/proof_time_overrun.cpp` on that commit. The planning code and the tests under `tests_r3_22/` were written for this tree. That proof was not copied in.

## What was wrong

Clock play (`wtime` / `btime`, increment, `movestogo`, Move Overhead) lives in `Worker::search`. The old allocation forced the usable time, the soft budget, and the hard budget up to at least 1 ms. When the clock was at or below Move Overhead, the engine still planned 1 ms, started helper threads, and searched. A 0 ms or 5 ms clock with a larger overhead then ran past the flag.

Increment is added to the soft budget. The hard budget is a fraction of the time left after overhead (60% in sudden death, 80% with `movestogo`), also capped at a multiple of soft. A large increment therefore made soft larger than hard. The audit's example is overhead 10, clock 100, increment 2000: soft was clamped to the 90 ms left, and hard was 54 ms.

## What changed

`plan_clock_budget` in `include/forge/clock_plan.hpp` is the clock planner. `Worker::search` calls it only for clock play. `go movetime` is unchanged.

Usable time is `max(0, time - overhead)`. Negative clocks, increments, and overheads count as zero.

- If usable time is 0, the plan is 0 ms soft and 0 ms hard. A hard limit of 0 would otherwise mean "not on a clock", so `clock_reserve_empty_` stops the search. The main thread returns the first legal move before any node, and helper threads are not started. Ponder still thinks on the opponent's clock until `ponderhit`, then stops.
- If usable time is positive, the previous sudden-death and `movestogo` formulas run, including the 1 ms floor. Hard is then kept inside `1 .. usable`, and soft is kept inside `1 .. hard`. When the old plan already had soft at or under hard, the numbers stay the same. When increment had pushed soft above hard, soft is lowered to hard. Hard itself is not raised.

The sudden-death coefficients are still the live tunables (`TmSoftDivisor` 22, `TmIncrementPercent` 75, `TmHardPercent` 60, `TmHardSoftMultiple` 5). `movestogo` still uses `increment * 3 / 4`, `available * 4 / 5`, and `soft * 4`, and still caps the move count at 50. A non-positive move count is still sudden death.

The iteration scale (`soft * factor` when the best move is stable or the eval falls) is unchanged. Because soft is now at most hard, and hard is at most the usable time, that scale can print a number above the hard limit only when the factor is above 1. The search still stops at the hard limit.

## Tests

`tests_r3_22/clock_plan_test.cpp` calls `plan_clock_budget` directly. For each overhead in `0, 1, 9, 10, 11, 50, 1000, 1000000000000`, and the parser ceiling `kMaxClockMs`, the clock, the increment, and moves-to-go each take `0, 1, overhead-1, overhead, overhead+1, 1000000000000, kMaxClockMs` (skipping an `overhead+1` that would not fit in a signed 64-bit integer). Every case checks:

- soft and hard are at least 0
- soft is at most hard
- both are at most `max(0, time - overhead)`
- a clock at or below overhead plans 0
- a positive usable clock plans at least 1 ms
- a plan that already obeyed the bounds matches the previous formulas
- a plan whose old soft exceeded hard keeps that hard limit and sets soft equal to it

Named cases cover the audit pair (clock 0 with overhead 10, clock 5 with overhead 50), clock 100 with increment 2000 (soft 54, hard 54), an ordinary minute, and the moves-to-go cap at 50. The run is `PASS clock plan checks 2413`, including an ASan and UBSan build of that file.

`tests_r3_22/clock_guard_test.cpp` links the engine. Empty reserves (the audit clocks, clock equal to overhead, and a 0/0 clock, on 1, 4, and 8 threads) return in 0 ms with 0 nodes and a legal move. A later depth-8 search on the same searcher is still 4099 nodes. Fixed searches match the counts measured before the change:

| search | nodes | move |
| --- | ---: | --- |
| start, depth 5 | 1001 | c2c4 |
| start, depth 8 | 4099 | d2d4 |
| kiwipete, depth 6 | 2279 | e2a6 |
| start, nodes 20000 | 20000 | d2d4 |
| kiwipete, nodes 12000 | 12000 | d5e6 |
| start, nodes 0 | 0 | a2a3 |

Ponder with clock 0 and overhead 10 searched, then stopped after `ponderhit` (2048 nodes in the release run). Live clocks of 80 ms, 100 ms plus a 2000 ms increment, and 300 ms with `movestogo` 5 all searched and stopped before depth 64. The same guard binary built with ASan and UBSan repeated those checks. The six fixed searches stayed on the counts above. The timed searches stopped earlier, which is the sanitizer slowdown, and the empty reserves still returned 0 nodes.

A depth-8 search with a 60 s clock still returned 4099 nodes and `d2d4`. A 20000-node search with that same clock still returned exactly 20000 nodes. An empty clock with Black to move returned 0 nodes.

Through UCI, with OwnBook off: `go wtime 0` at the default overhead, and `go wtime 5` with Move Overhead 50 and Threads 4, each printed `bestmove` and no `info depth` line. `go wtime 100 winc 2000` searched to depth 13 and stopped with the last info time at 39 ms, under the 54 ms hard limit for that plan.

## Pins

Threads 1, Hash 16, OwnBook false, before the change and again after it:

- `bench 11` = 312866
- `bench 13` = 862329
- `go perft 5` from the start position = 4865609

The same UCI depth and node searches as the table above matched the pre-change info lines and best moves. `movetime` was not retimed; that path is the old code.

Build used for the pins:

```bash
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=g++
cmake --build build -j
```

This machine's default `c++` is Clang 18, and it cannot see a C++ standard library for the GCC 14 installation it selects. g++ 13 with those flags produced the pins above.

Plan test:

```bash
g++ -std=c++20 -O2 -Wall -Wextra -Werror -I forge-combo29/include \
  forge-combo29/tests_r3_22/clock_plan_test.cpp -o /tmp/clock_plan_test
```

Guard test: the same `-D` flags and `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3` as the engine, plus `tests_r3_22/clock_guard_test.cpp` and the `src` translation units except `uci.cpp`.
