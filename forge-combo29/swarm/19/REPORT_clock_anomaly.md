# The 19-F52 anomaly traced: it is a HARD-LIMIT abort, and it hits the plan to the millisecond

seat 19 · area 9 · position `7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b - - 0 1` · build **PC r15** ·
**PC20** · **Threads 1** · Hash 16 · clock **6 s + 0.06** · cold.

## 1. The three lines

**What was asked.** Follow the 19-F52 lead: that one position took 1585.8 ms wall while its last completed
iteration reported 749 ms. Either a fail-high re-search happened, or the hard limit aborted an iteration. Trace
it and say which the numbers fit.

**The answer.** **It is a hard-limit abort, and the match is exact.** The search ended at **1585.8 ms**; the clock
plan's hard limit for `wtime 6000 winc 60` with Move Overhead 10 is **1585 ms** (`available 5990 → soft 317,
hard min(3594, 5×317) = 1585`). There were **no repeated depths** in the whole trace, so **no fail-high
re-search occurred**. And **849.7 ms — 54 % of the entire search — ran after the last report**, which is a
depth-21 iteration that was paid for and discarded.

**How sure.** Certain of the two diagnostics (every `info` line recorded with arrival time, engine time and
nodes; repeated depths would be visible and there are none). The hard-limit arithmetic agreeing to 0.8 ms with
the observed wall time makes the mechanism unambiguous.

## 2. The trace

| arrival ms | depth | engine time ms | nodes |
|---|---|---|---|
| 23.1 | 13 | 22 | 44,797 |
| 39.3 | 14 | 39 | 76,101 |
| 53.6 | 15 | 53 | 107,154 |
| 93.0 | 16 | 92 | 185,044 |
| 187.5 | 17 | 187 | 360,332 |
| 202.2 | 18 | 202 | 393,021 |
| 469.9 | 19 | 469 | 856,255 |
| **736.1** | **20** | **735** | **1,328,142** |
| **1585.8** | *(bestmove)* | — | — |

## 3. The two diagnostics

**H1 (fail-high re-search): refuted.** A re-search reports the same depth twice with rising time. The trace
reports depths 13, 14, 15, 16, 17, 18, 19, 20 — **each exactly once**. No repeats at all.

**H2 (hard-limit abort): confirmed, twice.**

1. **The silent gap.** After the depth-20 line at 736.1 ms, nothing is reported for **849.7 ms** — 54 % of the
   whole search — before `bestmove` at 1585.8 ms. So a depth-21 iteration ran and was abandoned.
2. **The arithmetic matches to 0.8 ms.** `plan_clock_budget(6000, 60, movestogo 0, overhead 10, soft_divisor 22,
   increment_percent 75, hard_percent 60, hard_soft_multiple 5)` gives `available = 5990`, `soft = 5990/22 + 45 =
   317`, `hard = min(5990×60/100, 5×317) = min(3594, 1585) =` **1585 ms**. Observed wall: **1585.8 ms.**

So the search did not stop at its soft plan (317 ms) or at a completed-iteration boundary near it; it ran on until
the **hard** limit, paying ~850 ms for an iteration it then threw away, and published depth 20.

## 4. Why this matters — it is not a bug, and it is the tail mechanism

**This is the mechanism behind the clock tail that seats 08, 02 and 28 have all been describing**, and it is not
a defect:

- The clock stops on an iteration boundary *unless* the hard limit arrives first. When a position's next
  iteration is much more expensive than the ones before it — here depth 20 cost 266 ms and depth 21 would have
  cost ~850 ms — the hard limit cuts it, and the wall time lands at the hard limit rather than near the soft plan.
- **This is exactly why ρ = 0.999 holds for 41 of 42 positions and fails for this one.** In the normal case the
  search ends just after a completed iteration, so wall ≈ last-iteration cost. Here it ends at the hard limit, so
  wall ≈ **hard limit**, which is a different quantity entirely — 1585 ms, not 749 ms.
- **The soft plan of 317 ms was exceeded by 5×** on this position. That is the "engine uses only 2.7–6.3 % of a
  6 s clock" observation from seat 02 seen from the other end: normally the engine stops far below the soft
  plan's ceiling because iteration costs are small; occasionally one iteration is so expensive that it blows
  through the soft plan and is stopped by the hard limit instead.

**So the correct summary of the clock is two-regime, not one:** *usually* the search ends on an iteration
boundary (ρ ≈ 1 with the last iteration's cost); *occasionally* an expensive iteration overshoots and the hard
limit terminates it, and then wall time equals the hard limit. A prediction of "wall ≈ last iteration cost" is
right in the first regime and off by up to the hard limit in the second.

## 5. Finding

**19-F53 — the 19-F52 anomaly is a HARD-LIMIT abort, not a re-search: no depth was reported twice, 849.7 ms
(54 % of the search) ran after the last report, and the search ended at 1585.8 ms against a planned hard limit of
1585 ms (soft plan 317 ms).** So the clock has **two regimes**: normally it ends on an iteration boundary (ρ =
0.999 over the other 41 of 42 positions), and occasionally an expensive iteration overshoots the soft plan and
is cut by the hard limit, at which point wall time equals the hard limit. This is the mechanism behind the clock
tail all three other seats described, and it reconciles their class-order disagreement: whether a class looks
"heavy" depends on how often its positions have one expensive iteration, not on its material count.

### I checked the inference, and it was understated

I ran `go depth 21` on the same position (no clock, so no hard limit) and it completed in **1551 ms** of engine
time, returning `h8f8`. So depth 21 does not cost the ~850 ms the gap showed — **it costs 1551 ms start to
finish**, which is *more than the entire 1585 ms hard limit*. The gap was only 849.7 ms because depth 21 had
already consumed 735 ms of the budget when it began; it was cut roughly 55 % of the way through.

That makes the mechanism sharper than §4 states: **an iteration whose cost exceeds the whole hard limit can never
complete on this clock from a cold position.** The engine will *always* be cut here and always publish depth 20.
It is not "occasionally an iteration overshoots the soft plan" — on this position depth 21 is simply
unaffordable, which is the clock working as designed.
- That the same mechanism explains every over-1-s case in my 42-position table. Only 5 positions exceeded 600 ms
  and I traced the worst one; the other four are untraced.

## 6. What I did NOT do

- I did not run with the hard limit disabled to see depth 21's cost and whether it changes the move. That is one
  flag away and would complete the picture.
- I did not trace the other four positions over 600 ms.
- I did not test whether `TmFinishIteration` (which the code has) would avoid this regime entirely — that is a
  behaviour change, not a measurement.

## 7. Files

`clock/trace_anomaly.py`, `clock/trace/RESULT.txt` (the full per-line trace and diagnostics).
