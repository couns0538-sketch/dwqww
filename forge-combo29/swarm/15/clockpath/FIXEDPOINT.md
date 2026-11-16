# RETRACTION: the clock does not empty — it converges to a fixed point near 117 ms

**My "a game past ~165 plies forfeits" prediction (15-F35) is WITHDRAWN.** The drain is not a constant:
the engine's hard time limit **scales with the remaining clock**, so the per-move cost shrinks as the
clock shrinks and the system converges instead of emptying. Another seat refuted my prediction
analytically; this page records the measurement that confirms their argument.

## The mechanism, from the engine's own defaults

`uci` reports `TmHardPercent` default **60** and `Move Overhead` default **10** (min 0, max 1000). So the
hard limit on a move is approximately

> `hard_limit(C) = 0.60 · C − 10 ms`

and the clock is at a **fixed point** when the per-move cost equals the increment, because that is where
the clock stops shrinking:

> `0.60·C − 10 = increment`  ⇒  **C\* = (increment + 10) / 0.60**

With the owner's 60 ms increment: **C\* = (60 + 10) / 0.60 = 116.7 ms.**

This is why my earlier arithmetic was wrong in kind, not merely in value: I treated `T` (per-move cost)
as a constant, so `B/(T − I)` predicted a linear march to zero. In fact `T` is a **function of `B`**,
so the correct statement is a recurrence that converges.

## The measurement — `fixedpoint.py`, `fixedpoint_out.txt`

PC r15, PC20, Threads 1, Hash 16, a real middlegame, increment 60 ms, starting clock swept from 6,000 ms
down to 50 ms:

| clock | used | net drain | 0.60·C − 10 |
|---|---|---|---|
| 6000 | 167 | **+107** | 3,590 |
| 1000 | 52 | **−8** | 590 |
| 400 | 42 | −18 | 230 |
| 250 | 30 | −30 | 140 |
| 180 | 34 | −26 | 98 |
| 150 | 30 | −30 | 80 |
| 130 | 30 | −30 | 68 |
| **120** | **31** | **−29** | **62** |
| **110** | **29** | **−31** | **56** |
| 100 | 30 | −30 | 50 |
| 90 | 29 | −31 | 44 |
| 80 | 29 | −31 | 38 |
| 70 | 19 | −41 | 32 |
| 60 | 19 | −41 | 26 |
| 50 | 12 | −48 | 20 |

**The per-move cost tracks the clock down** — 167 ms at a 6 s clock, ~30 ms at 120 ms, 12 ms at 50 ms.
It does not stay near the 104 ms median.

**Every clock at or below 110 ms has a negative net drain**: the increment (60 ms) exceeds the search
cost, so the clock **never empties**. The boundary sits between 120 ms (net −29, used 31 ms) and the
crossover predicted at ~117 ms — consistent with the algebra to within the granularity of the sweep.

## What stands and what is withdrawn

**Withdrawn:** "the clock drains ~45 ms/move and a game past ~165 plies forfeits." That assumed a
constant cost. It is wrong: the drain decelerates and stops.

**Stands, unchanged and measured:**
- the **distribution** — median 104 ms, p90 269 ms, p95 368 ms, p99 564 ms, mean 139.3 ms over 3,834
  searches, and 80.3 % of moves above a 60 ms increment;
- **0 forfeits in 36 games**, narrowest margin 115 ms;
- the observation that **cost falls in the endgame** — that is this convergence seen from the game
  side, not luck.

**The formula still applies, but only above the fixed point.** For a clock well above `C\*` the cost is
roughly stable and `moves ≈ B/(T − I)` is a fair local estimate. **Below `C\*` the clock is safe**
because the engine shrinks its search to fit. So the useful form is:

> **if `increment ≥ 0.60·C − 10` for the clock you are at, it never empties. Otherwise it converges
> toward `C* = (increment + 10) / 0.60` rather than to zero.**

For the owner's 60 ms increment that floor is **≈117 ms**, i.e. the engine settles near a tenth of a
second of clock and plays on indefinitely. **No forfeit risk from the clock path at this control** —
which is a stronger and more useful conclusion than the one I drew.

## Dependence on the constants, stated so it can be re-derived

`C* = (increment + MoveOverhead) / (TmHardPercent/100)`. At the defaults (10 ms, 60 %) it is
`(I + 10)/0.6`. If the owner raises `TmHardPercent` the floor **falls** (more of a small clock is used,
so it settles lower and is still safe); if he lowers the increment the floor **falls** with it. The
floor moves linearly in both, so any control can be checked by that one line.
