# All four budget modes on the PC's real path — and the answer to "which does the clock behave like"

**The question:** does the clock path behave like `nodes` (a ceiling), like `softnodes` (depth-complete),
or like neither?

**The answer: neither. The clock path is a THIRD kind** — it stops on its own time-management decision,
which in all 25 runs landed **far below** the budget it was given (0.4 %–6 % of a 6 s clock), and on a
one-legal-move position it exhausted the depth ladder (depth 64) in 22 ms regardless of whether the
budget was 100 ms or 6,000 ms.

PC build r15, **PC20**, **Threads 1**, Hash 16, 5 boards, 5 repeats each mode. Script `clockpath.py`.
Prediction committed and pushed before any measurement. Raw: `clock_out.txt`, `clock.jsonl`.

## The four modes side by side (median run of 5)

| board | `nodes 2000` | `softnodes 2000` | `movetime 100` | `wtime 6000+60` |
|---|---|---|---|---|
| startpos | d6, 1,740 n, **1 ms**, `c2c4` | d7, 4,121 n, **2 ms**, `d2d4` | d17, 166,281 n, **90 ms**, `d2d4` | d19, 650,246 n, **358 ms**, `e2e4` |
| G-mid-1 | d6, 1,574, 1 ms, `g7g6` | d7, 2,671, 2 ms, `g7g6` | d16, 170,070, 90 ms, `g7g6` | d18, 314,239, **158 ms**, `g7g6` |
| G-mid-2 | d7, 1,904, 1 ms, `b6b5` | d8, 3,312, 2 ms, `b6b5` | **d14/15**, 105,070–142,785, 90 ms, `b6b5` | d18, 514,093, 290 ms, `b6b5` |
| G-end-1 | d4, 1,667, 1 ms, `g6g7` | d5, 3,496, 2 ms, **`g6f6`** | d20, 391,675, 90 ms, `g6f7` | d28, 716,627, 148 ms, `g6f7` |
| G-end-2 | d6, 442, 1 ms, `a8b8` | d7, 2,025, 1 ms, `a8b8` | **d64**, 94,406, 22 ms, `a8b8` | **d64**, 94,406, 22 ms, `a8b8` |

## The character of each mode

| mode | what stops it | does it respect the budget? | deterministic? |
|---|---|---|---|
| `go nodes N` | node count | **yes, never exceeds** (down to −78 %) | yes |
| `go softnodes N` | end of the iteration that passes N | **no, always overshoots** except when the tree is small (up to +233 %) | yes |
| `go movetime T` | the engine's time management | **yes in the sense of never exceeding**, but it uses ~90 % of a short slice | mostly — 1 of 5 runs differed |
| `go wtime/btime/winc` | the engine's time management | **uses a small fraction** of a long clock (2.5 %–6 % of 6 s) | yes in 20 of 25 runs |

## Three findings, kept apart

### 1. The clock path is neither a ceiling nor depth-complete — it is time-management driven

`movetime 100` reliably used **90 ms of 100** (89–95 across all runs), so for a *short* budget the clock
is respected closely. But `wtime 6000 btime 6000 winc 60` used only **22–358 ms of 6,000** — between
**0.4 % and 6 %** of the clock. That is not a defect, it is the engine's own time management deciding the
position is decided or that a small slice suffices; but it means **a 6 s clock does not buy a 6 s
search**, and anyone estimating match cost from the clock would be wrong by an order of magnitude.

### 2. On a one-legal-move position the clock is irrelevant: the DEPTH LADDER ends first

G-end-2 (`k7/6R1/5N2/p4K1P/P7/8/8/8 b`, black has **one** legal move) gives **identical** results under
`movetime 100` and `wtime 6000+60`: **depth 64, 94,406 nodes, 22 ms, `mate -3`**, all 5 runs each. Depth
64 is the engine's clamp maximum, so the search exhausted the ladder in 22 ms and never consulted the
clock. Same shape as the 442-node `softnodes` case (15-F31): **when the tree is small, the budget is not
what stops the search.** 94,406 nodes in 22 ms is also why this position looked "under budget" earlier.

### 3. One genuine non-determinism, on a short time slice

G-mid-2 at `movetime 100`: **4 of 5 runs gave depth 15 / 142,785 nodes; 1 gave depth 14 / 105,070
nodes**, with the same wall time (90 ms) and the same move (`b6b5`). So the *move* is stable and the
*score* differs by 11 cp (`-251` vs `-262`) purely because one run fitted one fewer iteration into the
same 100 ms. That is the time-manager landing on either side of an iteration boundary. It is the only
non-determinism in 20 (board, mode) cells — and notably it does **not** happen at `wtime 6000+60`, where
all 5 runs agreed.

## My prediction, honestly

| # | prediction | verdict |
|---|---|---|
| P1 | clock wall time 0.5–6.0 s | **REFUTED** — all runs 22–358 ms; the engine uses 0.4 %–6 % of a 6 s clock |
| P2 | spread across 5 runs < 15 % of median | **HELD** (max 4.5 %) |
| P3 | legal bestmove in all 25 runs | **HELD** |
| P4 | no bogus mate score / no `0000` on a playable board | **HELD** |
| P5 | node counts vary ≥ 5 % across clock runs | **REFUTED as stated** — 19 of 20 cells gave IDENTICAL node counts; only G-mid-2 movetime varied (35.9 %) |

P1 and P5 were both wrong for the same reason: I assumed a clock search behaves like a budget-driven
search, consuming near its limit and varying run to run. In fact this engine's clock search is
**highly deterministic and thrifty** — it decides how long to think and then thinks that long, the same
way every time. That is a better property than I predicted, not a worse one.

## What this completes

All four budget modes on the owner's real path are now characterised on the same five boards:

- **want a hard compute ceiling** → `go nodes`
- **want a depth-complete soft budget** → `go softnodes` (budget "N plus the next depth")
- **want a time slice honoured closely** → `go movetime` (uses ~90 % of a short slice)
- **match play on a clock** → `go wtime/btime/winc`, which uses **2.5 %–6 % of a 6 s clock** and is
  deterministic run to run in 20 of 20 cells at that setting

## Scope

- 5 boards, one build, one regime, 5 repeats. Not a survey, and not a match.
- `movetime 100` is a *short* slice; I did not test `movetime 1000`, so "uses ~90 %" is a statement
  about short slices only.
- The 0.4 %–6 % observation on a 6 s clock is measured on five positions; it is not a claim about the
  time manager in general.
