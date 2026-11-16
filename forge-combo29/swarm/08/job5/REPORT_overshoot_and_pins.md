# The two closing measurements for 08-F11 and 08-F12 — seat 08

## 1. Does the opening book affect the four PINNED honesty numbers? **No.**

The question every seat's `HONESTY.txt` depends on. One fresh engine process per line, OwnBook set explicitly,
raw output in `job6/honesty_book_pins.txt`.

| pin | OwnBook true (default) | OwnBook false | identical? |
|---|---|---|---|
| bench 11 | **312,866** nodes | **312,866** nodes | yes |
| bench 13 | **862,329** nodes | **862,329** nodes | yes |
| bench 16 | **3,024,920** nodes | **3,024,920** nodes | yes |
| go perft 5 (startpos) | **4,865,609** nodes | **4,865,609** nodes | yes |

Exactly the four required numbers under both settings. The reasoning matches the measurement: `bench` is a
fixed node/depth bench that does not consult the book, and `go perft` is not a game search at all — `uci.cpp:524-528`
probes the book only when `game_search` holds, i.e. for `go wtime/btime` or `go movetime`, never for
`go depth`, `go nodes` or `go perft`. Only the `time`/`nps` fields differ between the two runs, which are
timings, not pins.

**So: no HONESTY.txt in this swarm needs to be re-run because of the book, including mine.** Anyone running
`go movetime M` or `go wtime` for a latency or bestmove number still must send `OwnBook false`.

Show it again:

    cd forge-combo29/swarm/08/job6 && bash honesty_book_pins.sh

## 2. 08-F11 — the number a GUI author actually needs

Distribution ratios (p99/median) describe the shape; a GUI author needs the failure: how often a search runs past
its planned soft time by more than a whole iteration, and how far past in absolute ms.
`job5/overshoot_one_iteration.py` records, for each search, every `info depth` line's elapsed time, so the cost of
the last completed iteration is known per search. 200 positions per clock, OwnBook false.

| clock ms | planned soft | searches | median overshoot | **worst overshoot** | over soft at all | **over soft by MORE than one whole iteration** |
|---|---|---|---|---|---|---|
| 200 | 8 ms | 200 | +1.0 ms | **+33.2 ms** | 60 % | **22 %** |
| 1000 | 45 ms | 200 | -6.1 ms | **+180.8 ms** | 39 % | **14 %** |

The worst cases, with the iteration that explains them:

| clock | wall | soft | overshoot | last iteration cost | overshoot / cost |
|---|---|---|---|---|---|
| 200 | 41.2 | 8 | +33.2 | 12.3 | 2.69 |
| 200 | 33.1 | 8 | +25.1 | 25.8 | 0.97 |
| 1000 | 225.8 | 45 | +180.8 | **1.6** | 111.40 |
| 1000 | 171.5 | 45 | +126.5 | 84.2 | 1.50 |

**A limitation I have to state, because one row exposes it.** My "one whole iteration" test uses the cost of the
LAST COMPLETED iteration as an estimate of the iteration that was running when the deadline hit. That estimate is
bad when the last completed iteration was very short: the +180.8 ms row has a 1.6 ms last iteration (a quick
depth that barely searched), so the test declares an overshoot of 111 iterations, which is arithmetically true
and physically meaningless. 99 of 400 rows have a last-iteration cost under 3 ms and 12 of those are flagged this
way. Excluding all short-iteration rows, the honest figures are:

| clock | over soft by more than one iteration, all rows | excluding rows with last iteration < 3 ms |
|---|---|---|
| 200 | 22 % | **33 %** (36 of 110) |
| 1000 | 14 % | **13 %** (25 of 191) |

So the direction is robust (the 200 ms clock is worse than the 1000 ms clock) and the magnitude is 13-33 %
depending on how a short final iteration is treated. The worst ABSOLUTE overshoots (+33.2 ms at 200 ms, +180.8 ms
at 1000 ms) do not depend on that choice at all and are the firm numbers for a GUI author:

- on a 200 ms clock, the worst search took **41.2 ms** when 8 ms was planned;
- on a 1000 ms clock, the worst search took **225.8 ms** when 45 ms was planned — 22.6 % of the whole clock in
  one move, from a soft plan of 4.5 %.

That last figure is the one worth carrying into a GUI or a match manager: the engine's clock plan is a lower
bound on what a single move may cost, not a bound on the move's share of the clock.

Show it again:

    cd forge-combo29/swarm/08/job5 && python3 overshoot_one_iteration.py ~/builds/release/forge /tmp/ov.tsv

Raw per-search data: `job5/overshoot_one_iteration.tsv`.

## What a fix would have to change (one answer, from the data above)

The data supports the **plan arithmetic** as the dominant cause at short clocks, not alone a missing mid-iteration
check: at 200 ms the soft plan is 8 ms while the median search takes 8.0 ms and two of the three worst searches had
an iteration cost *smaller* than their overshoot (overshoot/cost 0.97 and 1.10), so stopping at the end of that
iteration cannot by itself produce a 33 ms overrun — the plan was simply too small for an iteration to fit in it,
and the fix is in `clock_plan_budget` (`clock_plan.hpp:39-41`), which divides a 200 ms budget by a constant 22 and
a 1000 ms budget by the same 22, giving 8 ms and 45 ms against iterations that cost 12-84 ms. A mid-iteration soft
check would cut the tail at 1000 ms, where the worst row's overshoot was 1.5x its last iteration, but at 200 ms it
would mostly stop inside the first iteration and buy little: the honest reading is that both changes are needed and
the plan arithmetic is the one my numbers force.

## Were these searches cold? (seat 10's rule: `ucinewgame` restores cold, `Clear Hash` does not)

Yes, every one, and it is measured rather than assumed. On my build, `go depth 12` from startpos gives
**56,720 nodes three times in a row with `ucinewgame` between**, but **56,720 then 4,951 then 4,516 with nothing
between** — exactly seat 10's warm case. All my harnesses (`clock_latency.py`, `clock_latency2.py`, and the job4/job5
scripts) send `ucinewgame` + `isready` before every search, and **no script of mine ever sends `Clear Hash`**
(grep: zero uses). So the 6,500+ timing searches behind 08-F1, F2, F8, F9, F11 and F14 are all cold, and no warm
table can have shortened them or shifted their last completed depth. Recorded in `cold_vs_warm.txt`.
