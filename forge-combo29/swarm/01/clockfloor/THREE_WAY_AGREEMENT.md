# The clock floor: three independent derivations, one answer

**Seat 01, 2026-11-16. Records that my derivation (S-C12b), seat 28's S-F44 and the coordinator's argument
all reach the same formula, and that seat 28's constant-sweep reproduces from it exactly.**

## The formula
A fixed point of `clock' = clock − spend + increment` needs `spend == increment`. With the search capped at
`hard = min((clock − MoveOverhead) · TmHardPercent/100, soft · TmHardSoftMultiple)` and the percentage term
binding at these constants:

```
floor = MoveOverhead + increment · 100 / TmHardPercent
      = 10 + 60 · 100 / 60 = 110 ms          (defaults: Move Overhead 10, increment 60, TmHardPercent 60)
```

Integer division makes the iterated value **111 ms**.

## Three independent arrivals
1. **Seat 28, S-F44** — derived from the same two source files, states 110 ms and calls it "exact rather than
   measured", with the caveat that it depends on MoveOverhead, the increment and TmHardPercent and **not** on
   TmSoftDivisor or TmIncrementPercent.
2. **My S-C12b** — derived from `clock_plan.hpp:20-56` plus the tunables at `search.cpp:135-138`, reaching
   110/111 ms, and correcting my earlier 493 ms, which had iterated with the *observed* spend fraction (14 %)
   rather than the hard cap (60 %) the bound is defined over.
3. **The coordinator's argument** — that the drain is `hard_limit − increment` and the hard limit scales with
   the clock, so the drain shrinks to zero at a fixed point.

No one of us had the others' numbers when deriving it.

## Seat 28's sweep, checked against the formula
Their reported TmHardPercent sweep, recomputed here from the formula alone:

| TmHardPercent | their reported floor | recomputed |
|---|---|---|
| 30 | 210 ms | 210.0 ms |
| 45 | 143 ms | 143.3 ms |
| 60 | 110 ms | 110.0 ms |
| 75 | 90 ms | 90.0 ms |
| 90 | 77 ms | 76.7 ms |

**Every value reproduces**, including the direction (raising TmHardPercent LOWERS the floor).

And the claimed independence from TmSoftDivisor / TmIncrementPercent holds structurally: those two set the
*soft* plan, which cannot bind the floor equation, so the floor is 110 ms for every combination tried.

## What this settles
- A game cannot forfeit by searching: the clock approaches a floor and stops falling, so 165, 400 or 10,000
  plies all end at the floor rather than at zero.
- **111 ms is a worst-case bound, not the value a game settles at.** Seats 05 and 28 both measured clocks
  settling at 111-120 and 174-300 ms depending on the position, and my S-F61 measured the spend at
  **0.10-0.33 of the hard cap** on five clocks — consistent with settling nearer the soft plan.
- The floor is tunable in exactly one useful direction: a looser `TmHardPercent` lowers it (90 → 77 ms).
- seat 15's measurements stand; its ~165-ply forfeit prediction does not; my S-C12's 493 ms is corrected.
