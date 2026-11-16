# The "one p90 move from flagging" mechanism is WRONG — a clock search cannot flag on search time

I claimed in S-F39/S-F40 that a side at ~300 ms is one p90 search (262 ms) from flagging. **That is
arithmetically impossible**, and the constructed case confirms it. This file retracts the mechanism.

## Why it is impossible: the hard limit is a fraction of the remaining clock

A flag needs `wall > clock + increment`. Every clock search is capped by its hard plan, and from
`include/forge/clock_plan.hpp` with the engine's own constants:

```
available = clock - 10
hard      = min(available * 60/100, soft * 5)   ->  hard <= 0.60 * available
```

So the search can never spend more than **60 % of the remaining clock**, always well under
`clock + 60`. Measured across the clock range:

| clock ms | available | soft plan | hard plan | clock + 60 (flag threshold) | hard vs threshold | flag possible? |
|---|---|---|---|---|---|---|
| 3000 | 2990 | 180 | 900 | 3060 | BELOW | no |
| 1000 | 990 | 90 | 450 | 1060 | BELOW | no |
| 500 | 490 | 67 | 294 | 560 | BELOW | no |
| 300 | 290 | 58 | 174 | 360 | BELOW | no |
| 200 | 190 | 53 | 114 | 260 | BELOW | no |
| 150 | 140 | 51 | 84 | 210 | BELOW | no |
| 111 | 101 | 49 | 60 | 171 | BELOW | no |
| 60 | 50 | 30 | 30 | 120 | BELOW | no |
| 30 | 20 | 12 | 12 | 90 | BELOW | no |

**At no clock size can `hard` reach `clock + 60`.** A clock search therefore cannot lose the game on
search time. The only way a side flags is if the clock is *already* below zero from an earlier
accumulation, or if a move is played that consumes more than the clock before the search — neither of which
is a search-time event.

## The constructed case, as asked

Four complex middlegames (heavy pieces, open lines, many captures), each at clock 300 / 200 / 150 / 111 ms,
PC20, Threads 1:

| position | clock ms | plan hard | measured wall | clock+60 | flagged? | depth |
|---|---|---|---|---|---|---|
| sharp queen+rooks | 300 | 174 | 36 | 360 | no | 14 |
| sharp queen+rooks | 200 | 114 | 39 | 260 | no | 14 |
| sharp queen+rooks | 150 | 84 | 36 | 210 | no | 14 |
| sharp queen+rooks | 111 | 60 | 39 | 171 | no | 14 |
| opposite castling | 300 | 174 | 50 | 360 | no | 14 |
| opposite castling | 200 | 114 | 50 | 260 | no | 14 |
| opposite castling | 150 | 84 | 46 | 210 | no | 14 |
| opposite castling | 111 | 60 | 41 | 171 | no | 14 |
| many captures | 300 | 174 | 32 | 360 | no | 14 |
| many captures | 200 | 114 | 25 | 260 | no | 14 |
| many captures | 150 | 84 | 25 | 210 | no | 14 |
| many captures | 111 | 60 | 27 | 171 | no | 13 |
| open centre | 300 | 174 | 35 | 360 | no | 14 |
| open centre | 200 | 114 | 31 | 260 | no | 14 |
| open centre | 150 | 84 | 24 | 210 | no | 13 |
| open centre | 111 | 60 | 22 | 171 | no | 13 |

**Zero of 16 flagged**, and the measured walls (22-50 ms) are *far below even the hard plan* (60-174 ms) —
the engine finishes its ladder early and stops, so it does not even approach its own cap.

## What this means for the previous findings

- **S-F39 and S-F40's measurements stand**: median 99-132 ms, p90 262-359 ms, max 792 ms over 1,090 moves,
  zero flags. Those numbers were measured correctly.
- **Their interpretation does not.** "The margin is one p90 move" was wrong: at 111 ms the hard cap is
  60 ms, so the engine would spend at most 60 ms and its clock would go to 111 − 60 + 60 = 111 ms — flat,
  not negative. The p90 figure describes the *distribution of search times when the clock is large*, and
  does not apply at small clocks because the plan shrinks with the clock.
- **So the real reason the clock survives is structural, not adaptive luck**: `hard = 60 % of the clock`
  means spending is always proportional to what remains. That is a stronger and simpler statement than the
  one I made, and it is the one the owner should have.
- **What would flag:** a side only loses on time if a single move's *total* wall time exceeds
  `clock + 60`. With `hard <= 0.6 × clock` that requires the engine to violate its own plan, or a stall
  outside the search (process scheduling, GUI latency, a position the engine refuses). None of those is
  present in these runs, which is why 0 of 10 games flagged.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 transition_case.py ~/build/r15-pc/forge /tmp/t
```
Raw: `transition_case_out.txt`, `out_trans/transition.tsv`.
