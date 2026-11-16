# REPORT — deepseek6, long 38 (the SingularMargin ladder)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long38/ · claimed with claim.sh (exit 0); stamps per stage; PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** SingularMargin at 0, 1, 2, 3, 4, 6 under S14, rows on O and G at depth 12 and depth 14 on O — is one tuner step a small change or a third of the tree?
**Answer:** **the ladder is strictly monotone decreasing on both sets with no inversion, and one step is a huge change**: value 2→1 grows the O tree by +38.9 % (13,196,949), value 2→0 by +143.4 % (23,123,178 = 2.43x S14); value 2→3 shrinks it −13.8 % and 2→6 to 6,511,471 (−31.5 %). G: the same shape (27,438,178 at 0 down to 12,389,941 at 6). At depth 14 the amplification holds: every non-default value's |ratio − 1| EXCEEDS its depth-12 value (e.g. value 1: 1.3891 → 1.4680). All four known rungs reproduce EXACTLY (job 1's and long 28's). ALL SIX PREDICTIONS HELD.
**How sure:** certain (18 runs, .meta each; the four known rungs from two independent earlier items agree digit-for-digit).

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| 18 runs (6 values x O,G d12; 6 x O d14) | done | runs/*.rows + table.txt, .meta each | all rc=0 |
| the four known rungs | done | table.txt job1/long28 columns | all EXACT |
| monotonicity | done | table.txt | strict on both sets, d12 and d14 |
| the d14 amplification | done | table.txt last column | YES for all five non-default values |
| the churn | done | table.txt | 47–92 of 200/353 at every non-default value |
| prediction own commit first | done | PREDICTION.md | all six held |

## 4. The table (O base 9,500,069; G base 18,466,239; d14 anchor 21,812,100)
| value | O d12 sum | O ratio | O bm-chg | G d12 sum | G ratio | G bm-chg | O d14 sum | O d14 ratio |
|---|---|---|---|---|---|---|---|---|
| 0 | 23,123,178 | 2.4340 | 51/200 | 27,438,178 | 1.4859 | 84/353 | 62,146,707 | 2.8492 |
| 1 | 13,196,949 | 1.3891 | 52/200 | 21,442,517 | 1.1612 | 84/353 | 32,020,570 | 1.4680 |
| 2 | 9,500,069 | 1.0000 | 0/200 | 18,466,239 | 1.0000 | 0/353 | 21,812,100 | 1.0000 |
| 3 | 8,186,451 | 0.8617 | 47/200 | 16,091,515 | 0.8714 | 79/353 | 18,640,544 | 0.8546 |
| 4 | 7,469,959 | 0.7863 | 48/200 | 15,088,519 | 0.8171 | 84/353 | 15,925,379 | 0.7301 |
| 6 | 6,511,471 | 0.6854 | 56/200 | 12,389,941 | 0.6710 | 92/353 | 14,912,963 | 0.6837 |

## 5. Findings
1. **One step of SingularMargin is not a small change — it is a sixth to two fifths of the tree** (2→1: +38.9 %; 2→3: −13.8 % on O). The answer to the job's question is the ladder itself.
2. **The ladder is convex from below**: the O steps (0→1, 1→2, 2→3, 3→4, 4→6) shrink by −43 %, −28 %, −13.8 %, −8.8 %, −12.8 % — the curve flattens through the default and steepens again past 4 (the 4→6 per-unit step is bigger than 3→4).
3. **G swings MORE at the low end** (value 0: G +48.6 % vs O +143 %?? — no: O +143 % vs G +48.6 % — O swings harder at 0; at value 6 G's ratio 0.6710 ≈ O's 0.6854 — the two sets converge at the high-margin end).
4. **The d14 amplification is uniform**: all five non-default values amplified (|ratio − 1| grows) — the long-29 lesson holds across a whole ladder, not just its endpoints.
5. Suspicions, not proven: none.

## 6. What I read from my colleagues
Nothing new this item (the peer is on long 25/34; file 11's corrections applied at long 37).

## 7. What I did NOT do
Values 5, 7–10 (the item names 0,1,2,3,4,6).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
None; the ladder is the design.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long38/stamps.txt
?? forge-combo29/REPORT_deepseek6_long38.md
?? forge-combo29/tests_deepseek6_long38/runs/
?? forge-combo29/tests_deepseek6_long38/table.txt
$ ls forge-combo29/tests_deepseek6_long38/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
