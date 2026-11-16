# REPORT — seat 07, job 11: the clock in a GUI-style game, and the book trap

## What was asked / the answer / how sure

**Asked:** continue the area-7 read (the time manager is one of the eight files in the area's order),
prioritising what shows in normal play.

**Answer:** across nine time controls — including the nasty ones (`wtime 100`, `30`, `10`, `0`, and
`movestogo 1 / 2 / 40`) — the engine **never overran its remaining clock and never played an illegal
move**, and every search reported a real node count. I also found a measurement trap worth passing to
other seats: the built-in book answers clock searches and emits **no** `info depth` line, so a clock
harness that does not disable `OwnBook` silently measures book moves instead of searches.

**How sure:** high for no-overrun / no-illegal at these controls. Moderate for the general claim: I
tested nine controls of a few dozen plies each, on a 4-core box shared with other seats, so a very
rare overrun could be missed. The 5 ms slack in the overrun test is stated below.

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed.

## The test

`job11/clock_behaviour.py`: for each control it plays a self-game. Every move is
`position fen <current>`, `isready` to readyok, then `go wtime .. btime .. winc .. binc [movestogo ..]`.
The move the engine answers is played on a python-chess board and the side's clock is decremented by
the measured wall time plus the increment. Recorded per search: wall time (`go` sent → `bestmove`
read, monotonic), the engine's own `time` and `nodes`, legality of the move, and whether the wall time
exceeded the clock the engine had left.

**Overrun definition:** `wall_ms > left_ms + 5`. The 5 ms is measurement slack for this harness, not
an engine allowance — a real engine budget already subtracts `Move Overhead` (default 10 ms).

    sudden_1000    plies  24  overruns 0  rows without nodes 0  worst wall    138.9 ms
    sudden_10000   plies  24  overruns 0  rows without nodes 0  worst wall   2278.5 ms
    mtg_1          plies  12  overruns 0  rows without nodes 0  worst wall    593.3 ms
    mtg_2          plies  12  overruns 0  rows without nodes 0  worst wall    451.1 ms
    mtg_40         plies  16  overruns 0  rows without nodes 0  worst wall     62.5 ms
    tiny_100       plies  12  overruns 0  rows without nodes 0  worst wall     11.2 ms
    tiny_30        plies  10  overruns 0  rows without nodes 0  worst wall      1.8 ms
    tiny_10        plies   8  overruns 0  rows without nodes 0  worst wall      1.2 ms
    zero_0         plies   6  overruns 0  rows without nodes 0  worst wall      0.9 ms

Per-control tables: job11/raw/<control>.txt.

## The trap I fell into first, and why the numbers above are the real ones

My first run reported `rows without nodes 16` of 24 in *every* control — and my script still printed
"no overrun, no illegal move". Diagnosis: the engine was answering with a **book move**, and a book
move prints `info string book move ...` then `bestmove` with no `info depth` line at all. The book is
enabled by default (`OwnBook` default true) and applies precisely to clock searches
(`uci.cpp:525-527`: `game_search` = clock or movetime, not infinite, not ponder, no searchmoves, no
mate).

Two consequences, both fixed here:

1. **My test** now sets `OwnBook value false` and treats a missing nodes figure as a failure. Only
   then do all nine controls report `rows without nodes 0`.
2. **A general trap for the swarm:** any clock or movetime measurement that does not turn the book off
   is measuring book lookups, not searches, and any test that silently accepts a missing `info depth`
   line will report success while measuring nothing. This is the same class of error seat 19 flagged.

## Why `movestogo` looked wrong and is not

`mtg_2` row 3 showed 431 ms wall with the last reported iteration at `time 19`. That looked like a
discarded 400 ms iteration. Re-running the identical command with per-line timing:

    info depth 14 ... time 74
    info depth 15 ... time 136
    bestmove g1f3          (at 136.9 ms wall)

The 431 ms row was a different position in the self-game (the engine's own `time` field is per
search). The clock plan for `wtime 549 … movestogo 2` is soft ≈ 179 ms, hard ≈ 431 ms, and the search
stopped at 137 ms, comfortably inside both. No fault.

## Findings

**07-C7** in FINDINGS.md (clean clock result, plus the book caveat).

## Suspicions, not proven

- `plan_clock_budget` (include/forge/clock_plan.hpp) computes `hard = std::min(available * 4 / 5,
  soft * 4)` in the movestogo branch, and `soft` can exceed `hard` before both are clamped, after
  which `soft = hard`. Arithmetic-wise `available * 4` cannot overflow for the parse ceiling
  `kMaxClockMs = int64_max / 256`, so I found no overflow, but I did not prove the clamp order is
  intended rather than merely harmless.

## What I did NOT do

- Did not test book behaviour itself (only disabled it).
- Did not measure the 99th percentile of overruns over hundreds of searches (area 8's job).
- Did not test `movetime` in this loop; job1's edge cases covered `movetime 0/50/500`.

## What I am NOT sure about

- Whether a very short control (`wtime 10`) can overrun on a machine with other seats' load; my run
  had 4 cores shared with several agents.

## Times

See job11/stamps.txt.
