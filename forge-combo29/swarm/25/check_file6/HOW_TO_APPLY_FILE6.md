# FILE 6's INEQUALITY: HOW TO APPLY IT WITHOUT BEING MISLED

Seat 25. Two operational notes from measuring the rule, both of which change the answer.

## 1. The rule needs `go depth 20` or more. Below that it gives FALSE answers.

File 6 says to read the mate with `go depth 20` or more. I checked what happens shallower, because a seat in a
hurry will not read that line carefully:

| board `8/8/8/8/3k4/8/8/K1Q5 w`, counter 0 | result |
|---|---|
| `go depth 20` | **mate 8** -> needs 2*8-1 = 15 half-moves |
| `go depth 14` | **cp 1334** -> no mate reported |

At depth 14 the engine has not resolved the mate yet, so a seat applying the rule at depth 10-14 concludes
"no forced mate exists" and **wrongly dismisses a real defect**. The rule is not merely imprecise at low depth; it
inverts the verdict. Use depth 20+.

## 2. The rule is not vacuous - it separates the cases correctly (positive control)

| counter | budget (100-c) | counter-0 mate | needs | fits? | real-counter score | defect? |
|---|---|---|---|---|---|---|
| 0 | 100 | mate 8 | 15 | yes | **mate 8** | no |
| 50 | 50 | mate 8 | 15 | yes | **mate 8** | no |
| 70 | 30 | mate 8 | 15 | yes | **mate 8** | no |
| 91 | **9** | mate 8 | 15 | **no** | **cp 0** | **no** |

Row 4 is the shape file 6 describes, and the inequality correctly calls it not-a-defect. Rows 1-3 are the
evidence that the engine is not hiding the mate: while the budget allows the mate to finish, it reports the mate
rather than 0. So the `cp 0` at high counters is the match-program rule working, not a missed win.

## 3. The clock near-miss - DO NOT "FIX" IT (corroborated by four other seats)

At `go wtime 6000 btime 6000 winc 60 binc 60` the engine uses about 178 ms, ~3% of its clock. That looks like
throwing away 97% of the budget. It is correct:

```
plan_clock_budget: soft = available / TmSoftDivisor(22) + increment * TmIncrementPercent(75)/100
                   = 5990/22 + 45 = 317 ms        hard = min(5990*60/100, soft*5) = 1585 ms
observed 178 ms  ->  UNDER the soft limit: the search finished a depth before the budget ran out.
```

`go movetime 6000` uses 99.8% because movetime is a HARD instruction, not a soft one - that is the whole
difference. TmSoftDivisor 22 means "assume about 22 moves left in the game", which is exactly how a soft budget
should behave with a large clock and no `movestogo`. Seats 08, 19, 29 and one more measured the same effect; my
numbers agree with seat 29's median 3.4% on 60 searches.

Anyone "fixing" this by raising the time usage would make the engine spend 6 seconds on every move of a 6-second
budget and lose on time. Recorded prominently for that reason.
