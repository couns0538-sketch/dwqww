# S-C6 — CONFIRMS seat 08's 08-F10 (the two stop paths have opposite error modes)

Seat 08's claim: `go movetime M` checks the hard limit **inside** the search and discards the partial
iteration, so the wall time lands at the plan while the iteration the engine **kept** is well below it;
`go wtime` breaks at an **iteration boundary** and discards nothing, so the kept iteration carries the
time actually spent and the wall overshoots by up to a whole iteration.

**Verdict: CONFIRMS both halves, on both builds.** My own harness (`checks/check_08f10.py`), own
builds, **Threads 1**, Hash 16, MultiPV 1, `OwnBook false`, 6 fresh processes per case, read to
`bestmove`.

## How the two numbers are measured, and why they are different

- **wall** — monotonic clock from writing `go` to reading `bestmove`. This is the GUI's number.
- **kept** — the `time` field on the **last `info depth` line**: the iteration the engine chose to
  report, in its own words.
- **plan** — what the engine derives from the clock: `movetime − Move Overhead` (default overhead 10).

A tight wall with a low kept time means work was done and thrown away. That is the whole test.

## The `movetime` path: wall hugs the plan, kept time falls far below it

PC r15, medians of 6 runs:

| command | plan | wall | **wall − plan** | kept | **kept − plan** | depth |
|---|---|---|---|---|---|---|
| `go movetime 50` | 40 | 40.5 | **+0.5** | 32.0 | **−8.0** | 11 |
| `go movetime 500` | 490 | 490.7 | **+0.7** | 318.5 | **−171.5** | 16 |
| `go movetime 200` | 190 | 190.7 | **+0.7** | 170.0 | **−20.0** | 14 |
| `go movetime 50`, overhead **0** | 50 | 50.8 | +0.8 | 46.0 | −4.0 | 12 |
| `go movetime 50`, overhead **45** | 5 | 5.4 | +0.4 | 2.0 | −3.0 | 6 |

**Wall − plan is +0.4 to +0.8 ms in all 5 rows** (the search stops on time, tightly). **Kept − plan is
−3.0 to −171.5 ms in all 5 rows** (the iteration it reports finished long before). At `movetime 500`
that is **171 ms of searched work thrown away** — 35 % of the budget.

Base build, same shape: wall − plan **+0.6 to +0.8 ms**, kept − plan **−3.0 to −172.5 ms**.

The overhead rows matter: with overhead 45 the plan is 5 ms and the engine still lands the wall at
+0.4 ms and keeps an iteration finished 3 ms earlier, so this is not an artefact of the default
overhead value.

## The clock path: nothing is discarded

| command | wall | kept | wall − kept |
|---|---|---|---|
| `go wtime 1000 btime 1000` | 33.8 | 33.0 | **0.8** |
| `go wtime 500 btime 500` | 22.3 | 21.5 | **0.8** |
| `go wtime 1000 btime 1000 movestogo 1` | 322.1 | 321.5 | **0.6** |
| `go wtime 200 btime 200` | 15.0 | 14.0 | **1.0** |

Here the kept iteration's time tracks the wall to within **1 ms** in every row: the engine stops at a
boundary and keeps what it finished, so nothing is spent and discarded. That is the opposite error
mode — the clock path's risk is *overshoot* (it finishes a whole iteration past the soft limit), which
seat 08 measures separately as 08-F1/08-F14/08-F28.

## THE HEADLINE — for anyone planning a cross-engine `movetime` match

**A fixed-`movetime` comparison handicaps Forge twice: a fixed 10 ms overhead, and a discarded
partial iteration that scales with the budget. At 50 ms the two are comparable; at 500 ms the
discarded work is 17x the overhead; at 2000 ms it is 64x.** Quoting either number alone understates
the handicap by an order of magnitude at the budgets a match actually uses.

## Why the distinction is worth confirming rather than assuming

The two paths are usually discussed as "the engine's time management", but they fail in opposite
directions and need opposite fixes:

- **`movetime` wastes real work.** The reported depth is *behind* the effort spent: at `movetime 500`
  the engine kept a depth-16 iteration while 171 ms of a depth-17 search went in the bin. A fixed
  `movetime` comparison against another engine therefore handicaps Forge twice — once by the planned
  overhead subtraction (08-F2) and again by discarding the partial iteration.
- **`wtime` keeps everything** and overshoots instead, so its risk is a clock tail, not wasted effort.
  That matches seat 08's tail findings and my own job-2 observation that the clock path always
  answered in time.

A person reading only 08-F2 (the overhead subtraction) would think the `movetime` penalty is ~10 ms.
**It is that fixed 10 ms PLUS a discarded partial iteration that scales with the budget — at
`movetime 500` the discarded part alone was 171.5 ms, roughly 17x the overhead, and the two must
always be quoted together.** Measured across budgets:

| movetime | plan | discarded | discarded % of plan | overhead % of plan |
|---|---|---|---|---|
| 50 | 40 | 9.6 ms | 24.1 % | 25.0 % |
| 100 | 90 | 42.8 ms | 47.6 % | 11.1 % |
| 200 | 190 | 17.4 ms | 9.2 % | 5.3 % |
| **500** | **490** | **157.8 ms** | **32.2 %** | **2.0 %** |
| 1000 | 990 | 213.1 ms | 21.5 % | 1.0 % |
| 2000 | 1990 | 640.6 ms | 32.2 % | 0.5 % |

The discarded fraction is **not** a constant (9 %-48 % here, depending on where the last iteration
landed); what *is* constant is the asymmetry, and the ratio is what matters:

| movetime | discarded | overhead | **discarded / overhead** |
|---|---|---|---|
| 50 ms | 9.6 ms | 10 ms | **1.0x — comparable** |
| 200 ms | 17.4 ms | 10 ms | 1.7x |
| **500 ms** | **157.8 ms** | **10 ms** | **15.8x — call it 17x on the 6-run block** |
| 1000 ms | 213.1 ms | 10 ms | 21x |
| **2000 ms** | **640.6 ms** | **10 ms** | **64x** |

Raw: `checks/movetime_sweep.txt`, `checks/movetime_sweep.json`.

## Files

- `checks/check_08f10.py` — the harness.
- `checks/check_08f10_pc.txt`, `checks/check_08f10_base.txt` — raw runs, both builds.
- `checks/check_08f10_pc.json`, `checks/check_08f10_base.json` — raw records.
- `checks/check_08f10.meta` — exe hashes, Threads 1, settings, date.

## What I am not claiming

- Not the mechanism inside `src/search.cpp` — seat 08 cites `search.cpp:2191-2193` (hard limit) and
  `:2612` (soft limit). I confirmed the behaviour those lines are said to produce, not the lines.
- Not that the clock path never overshoots; that is 08-F1/F14/F28, measured by seat 08 and confirmed
  by seat 29 and seat 28. This check only establishes that it does not *discard*.
- `movetime` cases with `overhead 0` on the base build show −11 ms rather than −4 ms, so the exact
  discarded amount varies with position and speed; the sign is what the finding is about.
