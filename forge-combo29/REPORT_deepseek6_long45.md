# REPORT — deepseek6, long 45 (the eight biggest G-movers of longs 27/28 at depth 14 on G)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long45/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** the eight settings of longs 27/28 with the largest |ratio − 1| on G (one end each), G at depth 14 under S14 (S14 run twice first, the two sums equal), and whether the big G-movers grow or shrink with depth.
**Answer:** **the two base runs are EXACTLY equal (43,345,893 both) — the deterministic anchor — and the base sits at 2.347× the G depth-12 sum.** The answer to the question is the OPPOSITE of long 29's O-side finding: **on game positions the big movers' relative effects mostly FADE with depth — only 3 of 8 amplify (SingularMargin 1.1612→1.2775, IirDepth 1.0559→1.0835, RfpImproving 1.0204→1.0317), while SingularDepth's ratio FALLS (1.1459→1.1386) and four others shrink toward 1.** The top-two ordering (SingularMargin, SingularDepth) is preserved. Predictions: 1, 2, 5 held; 3 half-killed (SingularMargin yes, SingularDepth no); 4 killed (2 of 6, not 5).
**How sure:** certain of the ten runs (.meta each) and the twin-anchor equality.

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line first in stamps.txt) | done | stamps.txt | exit 0 |
| S14 on G at depth 14, TWICE | done | runs/base1.rows, runs/base2.rows | 43,345,893 == 43,345,893 EXACT |
| the eight setting runs | done | runs/*.rows + table.txt, .meta each | all rc=0 |
| the amplification scorecard | done | table.txt | 3 of 8 amplified on G (long 29's O: 15 of 19) |
| prediction own commit first | done | PREDICTION.md | 1, 2, 5 held; 3 half; 4 killed |

## 4. The table
| setting (end) | G d12 ratio | G d14 sum | G d14 ratio | amplified? |
|---|---|---|---|---|
| SingularMargin 1 | 1.1612 | 55,376,310 | 1.2775 | YES |
| SingularDepth 5 | 1.1459 | 49,355,138 | 1.1386 | no |
| LmrQuietDivisor 193 | 0.9293 | 41,320,169 | 0.9533 | no |
| LmrQuietBase 85 | 1.0682 | 45,613,591 | 1.0523 | no |
| IirDepth 3 | 1.0559 | 46,967,073 | 1.0835 | YES |
| RfpMargin 78 | 1.0564 | 44,911,714 | 1.0361 | no |
| LmpBase 7 | 0.9722 | 42,314,405 | 0.9762 | no |
| RfpImproving 34 | 1.0204 | 44,720,861 | 1.0317 | YES |

## 5. Findings
1. **Depth changes the sensitivity map differently on the two sets**: on O the small movers AMPLIFIED (long 29: 15/19); on G the big movers FADE (3/8 here) — a tuner's depth-12 importance ranking is not portable across depths or across position sets.
2. **The SingularMargin ladder's amplification is real and set-specific**: it amplified on G (1.28 at d14) AND on O (long 38's d14: value 1 = 1.4680) — the one setting that amplifies everywhere.
3. **The twin-anchor equality** (two S14 runs identical to the node) re-confirms the determinism of the whole G-side pipeline at depth 14 (43.3M nodes, twice).
4. Suspicions, not proven: the fade mechanism (the G positions' middlegame complexity dilutes the singular/extension effects at depth).

## 6. What I read from my colleagues
glmflash5's notes tail (its V5/C5 tree rows 9,163,379 / 9,170,430 at 2,000 nodes, ~3.5 % under S14 — its offer for my counter builds to locate the saving is queued behind the list); kimi5's branch state (no job-14 patch yet).

## 7. What I did NOT do
The O-side twin-anchor repeat (long 29's anchor ran once; the O determinism is established by years... by the whole series).

## 8. What I am NOT sure about
The fade mechanism (5.1).

## 9. A better way
None; the twin-anchor design was the item's own and it works.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long45/stamps.txt
?? forge-combo29/REPORT_deepseek6_long45.md
?? forge-combo29/tests_deepseek6_long45/runs/
?? forge-combo29/tests_deepseek6_long45/table.txt
$ ls forge-combo29/tests_deepseek6_long45/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
