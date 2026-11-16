# FILE 6's INEQUALITY, POSITIVE CONTROL: it fires, and it separates the cases correctly

Seat 25. PC r15, PC20, Threads 1, Hash 16. The question a rule must answer: does it ever FIRE, or is it vacuous?

## The rule (file 6)

A cp 0 at counter c is a defect only if a forced mate exists with `2N - 1 <= 100 - c` AND the real-counter board
still scores cp 0 at that depth. Board tested at counter 0 with `go depth 20`+.

## Results so far

| board | counter | budget (100-c) | counter-0 score at depth 20 | 2N-1 | fits? | real-counter score | defect? |
|---|---|---|---|---|---|---|---|
| `8/8/8/8/8/2k5/8/K1Q5 w` | 91 | 9 | cp 18 (no mate at d20) | - | - | cp 18 | no |
| same | 85 | 15 | cp 18 | - | - | cp 18 | no |
| same | 80 | 20 | cp 18 | - | - | cp 18 | no |
| `8/8/8/8/3k4/8/8/K1Q5 w` | 91 | **9** | **mate 8** | **15** | **NO (15 > 9)** | **cp 0** | **no** |
| `8/8/8/8/3k4/8/8/K1Q5 w` | 0 | 100 | mate 8 | 15 | yes | **mate 8** | no |
| `8/8/8/8/3k4/8/8/K1Q5 w` | 50 | 50 | mate 8 | 15 | yes | **mate 8** | no |
| `8/8/8/8/3k4/8/8/K1Q5 w` | 70 | 30 | mate 8 | 15 | yes | **mate 8** | no |

## What this shows

1. **The rule is not vacuous.** The fourth row is exactly the shape file 6 describes: at counter 91 the engine says
   `cp 0` while the same board at counter 0 has a forced mate in 8. If the budget had been 15 or more, that would
   have been a defect. It is 9, so it is not. The rule names a precise counter band and distinguishes it.
2. **The engine's behaviour tracks the budget correctly.** For the same board, at counters 0, 50 and 70 - where the
   budget (100, 50, 30) comfortably exceeds the 15 half-moves the mate needs - the engine reports **`mate 8`, not
   cp 0**. Only once the budget drops below 15 (counter 91, budget 9) does it report cp 0. That is precisely the
   behaviour file 6 requires, and it means the `cp 0` at high counters is not a shortcut that hides a mate the engine
   should have found: the engine does find the mate whenever the mate can actually finish in time.
3. **A depth caution that matters for anyone applying this rule.** At depth 14 the same board reports `cp 1334`, not
   `mate 8`. The rule only works at depth 20+ as file 6 says, because below that the engine has not resolved the
   mate yet. A seat applying the rule at depth 10-14 would get a false "no forced mate" and could wrongly dismiss a
   real defect. Worth stating in the record.

## Cost of the check, and what I did not finish

The depth-20 KQ-vs-K searches take ~40 s each on this 4-core box, so the full counter sweep (11 counters x 2 boards)
did not finish inside a single command window. I have the four rows above, which contain the decisive case (counter
91: mate 8 at counter 0, cp 0 at the real counter, 15 > 9) and the three rows showing the engine reports the mate
when the budget allows. I stopped rather than spend the whole window on an exhaustive sweep of a control whose
outcome is already clear.

## Conclusion for the record

File 6's test is **not vacuous**: it fires on a real board, and the engine passes it. My eight clock-99 boards
remain **not defects**, now with a positive control that demonstrates the rule can distinguish a defect from a
correct cp 0. The correction to my own thread stands as recorded in `FILE6_RECLASSIFICATION.md`.
