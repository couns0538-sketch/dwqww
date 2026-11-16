# The 2x2, completed on ONE instrument — and it WEAKENS the margin rule

S-C16 declined to build a 2x2 because seat 23's changed and unchanged halves used different instruments. This does
it properly with `gap_2x2.py`: their own 60 positions from `job10/out_60.json`, CHANGED/UNCHANGED classified from
THEIR recorded bestmoves at N = 20000/50000/250000 (18 changed, 42 unchanged — reproducing their split), and then
for **every** position, both halves, the top-two gap measured the same way: at the depth the 20000 budget actually
reached, scoring each of the top two moves alone with `go depth D searchmoves <move>`.

PC r15 + PC20, Threads 1, Hash 16, OwnBook false, cold, interactive driver.

## the completed table

| class | n | min gap | median gap | max gap | within 30 cp |
|---|---|---|---|---|---|
| CHANGED | 18 | 0 | **12** | 59 | **15 of 18 (83 %)** |
| UNCHANGED | 42 | 0 | **19** | 479 | **24 of 42 (57 %)** |

## the discriminating numbers

| threshold | precision | recall | true negatives |
|---|---|---|---|
| 10 cp | 38 % (6/16) | 33 % (6/18) | 32/42 |
| 20 cp | 37 % (13/35) | 72 % (13/18) | 20/42 |
| 30 cp | 38 % (15/39) | 83 % (15/18) | 18/42 |
| 50 cp | 32 % (16/50) | 89 % (16/50) | 8/42 |

## what this shows, including where it corrects the earlier claim
1. **The margin DOES separate the groups on average**: median 12 cp for changed vs 19 cp for unchanged. The
   direction is right and it is what seat 23 reported.
2. **But the separation is much weaker than the two-halves comparison suggested.** Seat 23 put unchanged at median
   103 cp; on the same instrument as the changed half, unchanged is **19 cp** — a far smaller difference, because
   the 103 came from comparing the best move against a RANDOM alternative, which inflates the gap enormously. **The
   "103 cp" figure was an artefact of that instrument, and the true unchanged gap is 19 cp.**
3. **As a per-position classifier the margin is weak** — precision 32-38 % at every threshold from 10 to 50 cp,
   which agrees with seat 23's own caveat (they measured 45-56 %) and confirms their caution rather than their
   headline. Recall is high (83 % at 30 cp) but a harness cannot use recall alone: it flags 21 of 42 unchanged
   positions as unsafe.
4. **The gap-0 case is 2 of 60 and splits 1 changed / 1 unchanged**, so my earlier "quiet ties change 67 % of the
   time" was built on three constructed boards and does not generalise to their game positions at this sample size.

## the corrected rule
**The margin is a weak per-position predictor.** It is directionally right — changed positions are closer on
average (12 vs 19 cp) — but precision is only ~38 %, so a small margin must NOT be treated as "this position will
change". What it IS good for: a LARGE margin (say over 100 cp, which in this sample is where the unchanged tail
lives up to 479 cp) is a reasonably safe sign, while a small margin tells you almost nothing about whether a
budget change will flip the move.

So the honest form for a harness is weaker than what I wrote in COMBINED_RULE.md: **do not rely on the margin to
predict budget sensitivity; the only reliable rule is that a forced answer (a found mate) never changes, and beyond
that you must re-run at the other budget rather than predict.**
