# FINDINGS — swarm 66 (clock behaviour)

Base tree `6b98f2170`. Build and re-run commands are in `STATUS.md`; every number in
`CLOCK_TABLE.md` has the script that produced it named here.

Each finding carries its **re-run command** and the **denominator as a literal**.

---

## F1 — A one-sided clock does not terminate at a real budget. It reached depth 39 and printed nothing.

`go wtime 300000` with **Black to move** (so `wtime` is the opponent's clock) ran for **288.7 s**, reached
**depth 39 / seldepth 56** and **416,554,567 nodes**, and was still searching when the harness stopped it.
It emitted **zero `info string` lines** — nothing in the output tells a GUI that a clock was ignored.

`parse_limits` (`src/uci.cpp`) assigns `limits.time_ms` only for the side to move:

```cpp
else if (token == "wtime") { const std::int64_t value = read_clock(); if (side == forge::White) limits.time_ms = value; }
else if (token == "btime") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.time_ms = value; }
```

So the search gets no clock at all and runs to `SearchLimits::depth = 64`. At 300 s it had not got there.

Control that makes this a measurement of the engine: the **same position** with `go btime 300000` (its own
clock) terminated by itself in **13.1 s at depth 31**; with `go btime 1000` in **31 ms at depth 14**. The
mirror case (`go btime 300000` with White to move) also never answered inside 3 s.

Answering the question directly: **it does not terminate; the only thing that ends it is `stop`.** The
depth-64 ceiling would bound it eventually, but that is a bound in tens of minutes to hours, not a clock.

Re-run:
```bash
python3 case1_opponent_clock.py /tmp/w66/build/forge 300   # ~5 min; prints 8/8 checks
```
Raw: `case1.json`. Denominators: 1 case, 2 mirror/own-clock controls, 8 checks.

---

## F2 — Large `movetime` is bounded by the clock, not by the 64-depth clamp. The 60% rule is a clock-path rule.

| movetime | wall | depth | wall/budget |
| ---: | ---: | ---: | ---: |
| 10 s | 9,990.6 ms | 27 | 1.000 |
| 30 s | 29,990.8 ms | 29 | 1.000 |
| 60 s | 59,990.9 ms | 30 | 1.000 |

All three stop on time, at depth 27–30, well short of 64 — so the two limits do not collide in the way the
brief anticipated: the depth clamp is not reached, and the time limit is what fires. On this path
`soft = hard = movetime - overhead`, so there is no 60% relationship to be preserved; the 60%
(`TmHardPercent`) rule lives in `plan_clock_budget`, which `movetime` does not call.

The control that proves the 60% rule exists on the other path: `go wtime 60000` stopped in **1.7–3.0 s**,
i.e. at the *soft* limit (`available/22` = 2727 ms), far below the 35,994 ms hard limit. That is the
2.5–13.7% utilisation in the brief, reproduced.

Re-run: `python3 case2_movetime.py /tmp/w66/build/forge 10000 30000 60000` — 11/11 checks, ~100 s.
Raw: `case2.json`. Denominators: 3 movetimes, 1 clock control, 11 checks.

---

## F3 — An increment larger than the clock is absorbed by pulling soft DOWN to hard; the engine does not over-think.

Clock 1000 ms, increment 2000 ms: uncapped soft = `990/22 + 2000*0.75` = 1545 ms against 990 ms
available. The plan clamps soft to available and then, because soft > hard, sets soft = hard = **594 ms**
(59.4% of the clock). Measured wall time 595 ms at depth 19. Every increment from 500 ms to 3,000,000,000 ms
gives the same 594 ms plan — the ladder is flat, and **no row plans the whole clock**.

Re-run: `python3 case3_increment_bigger_than_clock.py /tmp/w66/build/forge` — 21/21 checks, ~5 s.
Raw: `case3.json`. Denominators: 7 increments, 4 movestogo values, 21 checks.

---

## F4 — Zero and negative clocks answer a legal move in under 1.5 ms. No forfeit, no hang, 11 rows.

| go | wall | bestmove | legal |
| --- | ---: | --- | --- |
| `wtime 0` | 1.20 ms | d2d4 | yes |
| `wtime -100` | 0.37 ms | d2d4 | yes |
| `btime 0` (Black to move) | 0.56 ms | g8f6 | yes |
| `wtime 0 btime 0` | 0.14 ms | d2d4 | yes |
| `wtime 0 winc 5000` | 0.09 ms | d2d4 | yes |
| `wtime -3000000000` | 0.15 ms | d2d4 | yes |

Every position was accepted first (no `invalid FEN` in the position reply **or** the go output, and
python-chess accepts the same FEN), so "no search" cannot be a refused position. The control that proves the
harness can see a search at all: `wtime 11` (one millisecond past the 10 ms overhead) searched to depth 6
with 1,902 nodes.

Re-run: `python3 case4_zero_negative_clock.py /tmp/w66/build/forge` — 26/26 checks, ~3 s.
Raw: `case4.json`. Denominators: 11 clock rows, 26 checks.

### F4a — Correction to a value others may be carrying: `wtime 0` is not a 0-node reply, and the difference is the transposition table.

| table state | info lines | nodes | bestmove |
| --- | ---: | ---: | --- |
| cold (fresh process, first search of the process) | 1 | 26 | d2d4 |
| warm (after one `go depth 8`) | 0 | — | d2d4 |

12/12 in each arm. The mechanism is visible in `src/search.cpp`: on an empty reserve the engine plays the
TT hash move when one is legal (`result.nodes = 0`, no info line); otherwise it runs one ply capped at
`kEmergencyNodes = 2000`, and that ply can complete and print. **Both are deterministic given the table**,
so this is not a race — it is the table state. Anyone quoting "`wtime 0` returns the first legal move with
0 nodes" is quoting the warm case.

### F4b — A harness trap: `printf ... | ./forge` turns a `wtime 0` into a different answer.

| how stdin is fed | output |
| --- | --- |
| stdin held open after `go` | `info depth 1 ... nodes 26 ... pv d2d4`, then `bestmove d2d4` |
| stdin closed immediately (the usual pipe) | `bestmove a2a3`, **no info line at all** |

Closing stdin makes the engine see EOF, abort the search and fall back to the first legal move. `a2a3` is
*not* the engine's clock answer; it is its EOF answer. Several swarm scripts use the pipe form, so a
0-node/`a2a3` row anywhere in the swarm's tables should be re-checked with stdin held open.

---

## F5 — Very large clocks parse, clamp, and stay responsive. Nothing overflows.

`kMaxClockMs = int64_max / 256 = 36028797018963967`. Six tokens — 2000000000, 3000000000, int64-max,
the ceiling, one past the ceiling, and a 30-digit number — are all accepted. None answers inside an 8 s
probe (they are genuinely huge budgets), all answer an explicit `stop` with a legal move, and no row prints
an overflow or invalid diagnostic. On the same clocks `go ... depth 20` returns in 19–27 ms at depth 20, so
the depth ceiling still bounds the search.

Re-run: `python3 case5_huge_clock.py /tmp/w66/build/forge` — 27/27 checks, ~48 s (8 s probe per token).
Raw: `case5.json`. Denominators: 6 clock tokens, 2 depth-probes, 1 control, 27 checks.

---

## F6 — Repeated `go` on the same clock does not drain: N repeats buy N full plans from one clock value.

Six repeats of `go wtime 1000` with no move played cost **485 ms total** (25–140 ms each), each planning
from the same 1000 ms. `go movetime 200` repeated six times spent 190.4–190.8 ms each time.

This is correct behaviour for a stateless clock protocol — the engine cannot know the GUI is not playing —
but it is worth stating because it is what an analysis GUI does: a GUI that re-sends its original clock on
every `go` gets an unlimited number of full budgets.

Control that the measurement is not TT warmth: `go depth 12` after `ucinewgame` gives 56720 nodes three
times; without `ucinewgame` it gives 56720, then 4951, then 4516. **`ucinewgame` is mandatory for
comparable node counts** — anyone comparing node counts across searches in one process without it is
measuring the table.

Re-run: `python3 case6_repeated_go.py /tmp/w66/build/forge 6` — 15/15 checks, ~2 s.
Raw: `case6.json`. Denominators: 6 repeats, 6 movetime repeats, 3 ucinewgame repeats, 15 checks.

---

## F7 — At 3+2 the clock GROWS, so playing at that control cannot confirm a floor.

Measured on the first 3+2 self-play game (91 plies, 179.4 s): the clock started at 3000 ms and never fell
below **3000 ms**, reaching ~3900 ms by the end. The engine's per-move spend (~1.0–2.3 s) is smaller than
the 2000 ms increment, so the increment out-paces the spend and the remaining time rises.

Consequence for the brief's item 7: **20 games at 3+2 confirm the zero-forfeit result but cannot confirm
the floor at 111 ms**, because the clock never approaches it. A floor test needs a control that actually
drains, so this audit adds one: charge the engine 10x its think time plus 200 ms per move against a 3+2
clock. With an increment that drain reaches **clock 0** and the engine still answers a legal move in
**0.1–0.6 ms** for every one of 60 plies; with the increment removed it reaches 0 after a 209 ms move at
depth 13. All 60 moves legal in both arms, no hang, no illegal move.

Re-run: `python3 case7_game_driver.py /tmp/w66/build/forge 20 3000 2000`.

---

## What this audit did NOT find

- No forfeit in any case (11 zero/negative rows, 7 increment rows, 6 huge clocks, 6 repeated goes,
  60 drain plies, and the 3+2 match).
- No hang in any case that had a clock. The only non-termination is F1, the one-sided clock.
- No illegal `bestmove` and no refused position anywhere: every FEN and every move list was validated with
  python-chess before sending, and both reply streams were scanned for `invalid FEN` (0 hits).

## Harness self-audit

`selftest.py` plants four faults and requires each to be caught: a hanging engine, an engine that emits an
`invalid FEN` line **only** in the position reply (correctly invisible in the go output — which is why both
streams are scanned), a 350 ms delay, and a multi-line info stream where only the last depth counts. It also
proves the FEN validator rejects an empty board and an illegal move.

It scores **11/11 against the real engine** and **10/11 with exit code 1 against a deliberately lying fake
engine**, so it is a test that can fail.

Two of my own checks were wrong on first run and are recorded rather than quietly fixed: a repeated-`go`
check that compared the total against the clock instead of against the per-go mean (it failed at 0.5x and
the engine was right), and a TT-warmth control that omitted `ucinewgame` (it failed because the table was
warm, which is what produced F6's control).
