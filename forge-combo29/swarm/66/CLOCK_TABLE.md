# CLOCK_TABLE — swarm 66

Every row is one `go` on the base-tree build (`6b98f2170`, g++-13 Release, `-DFORGE_MARCH=native`,
binary `/tmp/w66/build/forge`, `bench 11` = 312866 reproduced). Threads 1, Hash 32, OwnBook false,
Move Overhead at its default 10 ms unless the row says otherwise.

Columns:
- **wall** — measured from writing `go` to receiving `bestmove`, on the harness's monotonic clock.
- **budget** — the limit the formula in `include/forge/clock_plan.hpp` gives for that row.
- **wall/budget** — 1.0 means the row spent its entire plan. Values well under 1 are the normal
  case: the soft budget binds before the hard one.
- **depth / nodes** — from the last `info depth` line the engine printed.

## Case 1 — opponent's clock only (the side-to-move's clock is absent)

| go | side to move | wall | depth | nodes | terminated by itself | diagnostics |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `go wtime 300000` | Black | **330.0 s (the whole allowance; no `bestmove`)** | **39** | 416,554,567 | **NO** — needed `stop` | **none** |
| `go btime 300000` | White | >3 s (probe cap) | — | — | NO | none |
| `go btime 1000` (own clock) | Black | 0.022 s | 18 | — | yes | none |
| `go btime 300000` (own clock) | Black | 8.1 s | 31 | — | yes | none |

The two control rows are the same position and the same budget, with the clock belonging to the side to
move. They terminate; the top row does not. That contrast is what makes the top row a measurement of the
engine and not of the harness.

## Case 2 — large `movetime`

`movetime` sets `soft = hard = max(1, movetime - overhead)`; there is no 60% rule on this path.

| go | wall | depth | seldepth | nodes | wall/budget |
| --- | ---: | ---: | ---: | ---: | ---: |
| `go movetime 10000` | 9,990.2 ms | 27 | 38 | 13,206,934 | 1.000 |
| `go movetime 30000` | 29,991.0 ms | 30 | 50 | 44,942,225 | 1.000 |
| `go movetime 60000` | 59,991.0 ms | 32 | 45 | 20,819,104 | 1.000 |
| `go wtime 60000` (clock control) | 1,671 ms | 26 | — | — | 0.05 of the 35,994 ms hard |

The depth-64 clamp is never reached at these budgets: all three stop on time, at depth 27–32. The clock
control shows the 60% hard limit exists but is not what binds — the soft budget (`available/22` = 2726.8 ms)
is, and it fired at 1,671 ms.

## Case 3 — increment larger than the clock

Clock 1000 ms, overhead 10, so `available` = 990 ms.

| increment | plan soft | plan hard | hard as % of clock | wall | depth |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 45 | 225 | 22.5% | 60.5 ms | 14 |
| 500 | 420 | 594 | 59.4% | 538.9 ms | 19 |
| 1000 | 594 | 594 | 59.4% | 401.0 ms | 20 |
| 2000 | 594 | 594 | 59.4% | 594.3 ms | 19 |
| 5000 | 594 | 594 | 59.4% | 392.7 ms | 19 |
| 60000 | 594 | 594 | 59.4% | 589.3 ms | 20 |
| 3000000000 | 594 | 594 | 59.4% | 542.3 ms | 20 |

At increment 0 the soft limit (45 ms) binds long before the hard one (225 ms), which is why that row spent
60 ms rather than 225. From increment 500 upward the hard limit is the binding one and every row sits at
594 ms.

Uncapped sudden-death soft for increment 2000 is `990/22 + 2000*0.75` = 1545 ms, which exceeds both the
990 ms available and the 594 ms hard limit. The plan clamps soft to `available` and then pulls it down to
hard, so soft == hard == 594. A larger increment therefore does **not** raise the budget: the ladder is
flat from 500 upward, and no row plans the whole clock.

## Case 4 — zero and negative clocks

Every row's position was accepted (no `invalid FEN` in either the position reply or the go output, and
python-chess accepts the same FEN), so a missing search cannot be a refused position.

| go | side to move | wall | info lines | depth | nodes | bestmove | legal |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `wtime 0` | White | 0.59 ms | 1 | 1 | 26 | d2d4 | yes |
| `wtime -100` | White | 0.07 ms | 0 | — | — | d2d4 | yes |
| `btime 0` | Black | 0.12 ms | 1 | 1 | 29 | g8f6 | yes |
| `wtime 0 btime 0` | White | 0.07 ms | 0 | — | — | d2d4 | yes |
| `wtime 0 winc 5000` | White | 0.06 ms | 0 | — | — | d2d4 | yes |
| `wtime 5` | White | 0.06 ms | 0 | — | — | d2d4 | yes |
| `wtime 10` (== overhead) | White | 0.06 ms | 0 | — | — | d2d4 | yes |
| `wtime 11` (one past) | White | 1.15 ms | 6 | 6 | 1,902 | d2d4 | yes |
| `wtime 1000 winc -500` | White | 95.88 ms | 15 | 15 | 159,518 | d2d4 | yes |
| `btime -100` (opponent clock) | White | 3,000 ms, `stop` | 22 | 22 | 2,479,831 | d2d4 | yes |
| `wtime -3000000000` | White | 0.15 ms | 0 | — | — | d2d4 | yes |

No forfeit, no hang, no illegal move, in any row. The `btime -100` row is the one that does not stop by
itself — not because the value is negative but because it is the **opponent's** clock, i.e. case 1 again.

### The info-line count on an empty reserve is TT-dependent, not random

`wtime 0` printed one depth-1 line (26 nodes) on a cold table and zero lines on a warm one, 12 times each:

| table state | info lines | nodes | bestmove |
| --- | ---: | ---: | --- |
| cold (fresh process, first search) | 1 | 26 | d2d4 |
| warm (after one `go depth 8`) | 0 | — | d2d4 |

Source: `src/search.cpp` — on an empty reserve the engine plays the TT hash move when one is legal
(0 nodes, no info line); otherwise it searches one ply capped at 2000 nodes (`kEmergencyNodes`), and that
ply can complete and print. Both branches are deterministic given the table; the outcome differs only
because the table differs.

## Case 5 — very large clocks

| clock token | parsed as | plan hard | answers in 8 s | answers `stop` | `depth 20` on the same clock |
| --- | ---: | ---: | --- | --- | --- |
| 2000000000 | 2000000000 | 1,199,999,994 | no (depth 26 when probed) | yes, legal | depth 20 |
| 3000000000 | 3000000000 | 1,799,999,994 | no (depth 27) | yes, legal | — |
| 9223372036854775807 | 36028797018963967 | 21,617,278,211,378,380 | no (depth 26) | yes, legal | depth 20 |
| 36028797018963967 | 36028797018963967 | 21,617,278,211,378,380 | no (depth 28) | yes, legal | — |
| 36028797018963968 | 36028797018963967 | 21,617,278,211,378,380 | no (depth 28) | yes, legal | — |
| 999999999999999999999999999999 | 36028797018963967 | 21,617,278,211,378,380 | no (depth 27) | yes, legal | — |

`kMaxClockMs = int64_max/256 = 36028797018963967` (`include/forge/uci_clock.hpp`). Nothing overflows,
nothing answers instantly, and an explicit `stop` always produces a legal move. A huge clock does not make
the engine unresponsive: `depth 20` on the same clock returns in 19–27 ms, so the depth ceiling binds.

## Case 6 — repeated `go` on the same clock

Six repeats of `go wtime 1000`, no move played, `position startpos` before each:

| repeat | wall | depth |
| ---: | ---: | ---: |
| 1 | 68 ms | 14 |
| 2 | 98 ms | 15 |
| 3 | 97 ms | 16 |
| 4 | 56 ms | 17 |
| 5 | 140 ms | 18 |
| 6 | 25 ms | 17 |
| **total** | **485 ms** | — |

Nothing accumulates and nothing decays: each repeat plans from the same 1000 ms. The GUI spent 485 ms of
wall time having told the engine the clock was 1000 ms six times. `go movetime 200` repeated six times
spent 190.4–190.8 ms each time — the movetime path is immune to any drain by construction.

## Case 7 — a real accumulating clock

All at Threads 1, Hash 32, OwnBook false, Move Overhead 10, seeded opening set, python-chess validating
every position and every bestmove.

### 20 games at 1000+100 ms (the control that actually reaches the floor)

| measure | value |
| --- | ---: |
| games completed | 20 of 20 |
| plies played | 3,071 |
| forfeits | **0** |
| hangs (no bestmove) | **0** |
| illegal bestmoves | **0** |
| refused positions (`invalid FEN`) | **0** |
| **max move time / clock available** | **0.5937** |
| p99 of the same ratio | 0.5895 |
| median of the same ratio | 0.1499 |
| lowest clock any game reached | 176 ms |
| moves made at a clock of ≤200 ms | 63 |
| worst overshoot of the predicted hard limit | **+2.1 ms** over 3,071 moves |
| closest approach to the predicted hard limit | 1.012 (clock 306 → charged 179.1 ms vs hard 177 ms) |

Spend by clock bucket (`case7_analyse.py`, which recomputes all of this from the committed JSON):

| clock bucket | moves | max spent | median spent |
| --- | ---: | ---: | ---: |
| ≤200 ms | 63 | 114.5 ms | 99.5 ms |
| 201–400 ms | 629 | 228.7 ms | 79.1 ms |
| 401–700 ms | 1,248 | 402.2 ms | 79.3 ms |
| 701–1000 ms | 866 | 510.6 ms | 89.7 ms |
| >1000 ms | 265 | 620.9 ms | 87.6 ms |

The floor is visible in the top row: with a clock at or below 200 ms the worst move spent 114.5 ms, which
is `0.6 × (200 − 10)` = 114 ms — the 60% hard cap computed from `available`, to within a millisecond. The
largest spend on the whole match is 620.9 ms, never the whole clock.

### 20 games at 3000+2000 ms (3+2, the brief's control) — COMPLETE

| measure | value |
| --- | ---: |
| games complete | **20 of 20** |
| plies | **2,604** |
| forfeits / hangs / illegal / refused | **0 / 0 / 0 / 0** |
| max (move time ÷ clock available) | **0.5997** |
| median of that ratio | 0.1850 |
| worst overshoot of the predicted hard limit | **+1.7 ms** over 2,604 moves |
| closest approach to the predicted hard limit | 1.001 |
| lowest clock reached | **3000 ms** — never below the starting value |
| moves at a clock ≤200 ms | **0 of 2,604** |

Every one of the 2,604 moves was made at a clock above 1000 ms, so this control exercised exactly one clock
bucket. Two things it establishes and one it cannot:

1. The zero-forfeit result holds over **20 games / 2,604 plies** at a control 3× slower than any previously
   tested, and every move obeys the plan formula (max 0.5997 of available, +1.7 ms worst overshoot).
2. The clock **grows**: not one of 2,604 moves was made at a clock below 3000 ms, and the largest single
   spend in the whole set (11,107.2 ms) was made from an **18,521 ms** clock, where the formula's hard limit
   is 11,106 ms — even the set's most expensive move is the cap, not a runaway.
3. It **cannot** confirm the floor. `0 of 2,604 moves at ≤200 ms` is the measurement that says so rather
   than an inference, and it is why the 1000+100 match and the drain control exist.

### Drain control (the only way to reach the floor at a 3+2 clock)

Charge the engine 10× its own think time + 200 ms per move against a 3+2 clock.

| arm | plies | lowest clock before a move | all moves legal | hangs |
| --- | ---: | ---: | --- | --- |
| 10× + 200 ms, increment 2000 | 60 | **0 ms** | yes (60/60) | none |
| 10× + 200 ms, increment 0 | 60 | **0 ms** | yes (60/60) | none |

At a clock of 0 the engine answered in 0.1–0.6 ms every time, legally, with no hang. A weaker 2× drain
reached equilibrium at 1376 ms and never went lower — the engine's spend falls as its clock falls, so a
mild overcharge cannot drain it. That is itself worth knowing: the planner is self-limiting.

