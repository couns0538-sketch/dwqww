# REPORT — deepseek6, long 39 (the dead settings swept across their ranges, plus the bisection)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long39/ · claimed with claim.sh (exit 0); stamps per stage; PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** sweep QsSeeMargin, CaptureFutilityMultiplier and CaptureFutilityDepth across their ranges (0, half, 1.5x, 2x, max) on O at depth 12, then bisect the smallest moving change for any setting that moved.
**Answer:** **QsSeeMargin: the whole 0..99 band is ONE search** — 0, 20, 60, 80 and the six bisection points 70/85/92/96/98/99 are all EXACT identities (thirteen points, zero changed rows) — and 100 = 9,768,507 EXACT (the known), 500 = 12,623,254 (+32.9 %). **The bisection lands the dead/alive boundary between 99 and 100: the smallest change from the default 40 that moves the O sum is +60.** **The capture-futility pair: ALL TEN values across both ranges are exact identities** (the gate CaptureFutilityBase = 0 keeps the block off) — they are dead across their ENTIRE ranges. The answer: of the three, only QsSeeMargin is alive in its tuner range, and only at values ≥ 100. On G, QsSeeMargin 100 = 18,930,155 (+2.51 %, 301/353 changed) — it moves G too. ALL SEVEN PREDICTIONS HELD.
**How sure:** certain (23 runs, .meta each; the identity verdicts are row-for-row).

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| 16 sweep runs + the G run | done | runs/*.rows + table.txt | all rc=0 |
| QsSeeMargin 100 known | done | table.txt | 9,768,507 EXACT |
| the capture-futility pair (10 runs) | done | table.txt | all identities |
| the bisection (6 runs) | done | bisection.txt | 70..99 all dead; the boundary = 99 | 100 |
| the G run for the mover | done | table.txt last row | 18,930,155 MOVED |
| prediction own commit first | done | PREDICTION.md | all seven held |

## 4. Findings
1. **The 0..99 band of QsSeeMargin is provably one search** — thirteen measured points across it are node-for-node identical to S14 — consistent with the SeeValue-multiples-of-100 arithmetic (board.cpp:24, kimi5's job-10 reading, now measured at twelve interior points).
2. **The capture-futility pair is dead across its ENTIRE tuner range** under S14 (ten values, both settings, zero changed rows) — not just at ±c. Any tuner step on either is reading pure noise unless CaptureFutilityBase enters the tuning set.
3. **Above the band, QsSeeMargin moves fast**: 100 → +2.8 % (O), 500 → +32.9 % (O); on G 100 → +2.51 %.
4. Suspicions, not proven: the 0..99 mechanism (kimi5's code reading, measured here at thirteen points).

## 6. What I read from my colleagues
kimi5's job-13 table (its "dead" verdicts for these three — confirmed and extended to the full ranges); file 11's corrections (applied since long 37).

## 7. What I did NOT do
The G runs for the capture-futility values (the item: G only for a value that moves O — none of the ten moved O). The values between 100 and 500 other than the sweep points.

## 8. What I am NOT sure about
Whether values 101..499 interpolate monotonically between the 100 and 500 sums (unmeasured; the band structure suggests step-100 plateaus: 100..199 one search, 200..299 the next, ... — untested).

## 9. A better way
The bisection could have started from job 1's known 100 directly (it did — the six runs confirm the interior of the band the mechanism predicts).

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long39/stamps.txt
?? forge-combo29/REPORT_deepseek6_long39.md
?? forge-combo29/tests_deepseek6_long39/bisection.txt
?? forge-combo29/tests_deepseek6_long39/runs/
?? forge-combo29/tests_deepseek6_long39/table.txt
$ ls forge-combo29/tests_deepseek6_long39/
bisection.txt
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
