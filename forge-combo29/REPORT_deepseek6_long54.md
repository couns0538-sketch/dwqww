# REPORT — deepseek6, long 54 (depth 16 on the first 100 of G)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long54/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** S14 (run twice, must be equal), SingularMargin 1 and SingularDepth 5 on the first 100 of G at depth 16, beside long 45's depth-14 ratios — do the two keep their size at depth 16.
**Answer:** the twin S14 runs are EXACTLY equal (25,533,430 both). **The two settings diverge: SingularMargin 1's ratio FADES (1.2775 at depth 14 → 1.2477 at 16) while SingularDepth 5 creeps up (1.1386 → 1.1421); SingularMargin stays the bigger.** Predictions: 1, 4, 5 held; 3 killed (the fade); 2 KILLED BY MY OWN ARITHMETIC ERROR — I compared a 100-position depth-16 sum against a 353-position depth-14 anchor ([92M, 112M]); the honest per-position growth is ~4.9x from depth 12 to 16 (255k vs 52k nodes per position), well inside any sane band.
**How sure:** certain of the four runs (.meta each) and the twin equality; the ratio comparisons are against long 45's depth-14 ratios (which were measured on all 353 — the position-count difference is stated).

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| the four depth-16 runs (first 100 of G) | done | runs/*.rows + table.txt, .meta each | all rc=0 |
| the twin equality | done | table.txt first line | EXACT |
| the ratio comparisons | done | table.txt | SingularMargin fades; SingularDepth creeps up |
| prediction own commit first | done | PREDICTION.md | 1, 4, 5 held; 3 killed; 2 killed (my arithmetic: 100-position vs 353-position totals) |

## 4. The table
| setting | d16 sum (first 100 of G) | d16 ratio vs the twin base | d14 ratio (long 45, all 353) | grew? |
|---|---|---|---|---|
| S14 (twice) | 25,533,430 = 25,533,430 | 1.0000 | — | — |
| SingularMargin 1 | 31,857,253 | 1.2477 | 1.2775 | no |
| SingularDepth 5 | 29,161,243 | 1.1421 | 1.1386 | YES |

## 5. Findings
1. **The two biggest G-movers separate at depth 16**: SingularMargin's relative effect fades past depth 14 while SingularDepth's keeps creeping — the "which mover survives depth" answer changes at 16.
2. **The determinism holds at depth 16** (the twin runs identical at 25.5M nodes).
3. Suspicions, not proven: the fade mechanism (the singular re-searches' share peaks in the mid-game depth band).

## 6. What I read from my colleagues
Nothing new this item.

## 7. What I did NOT do
The full-G depth-16 run (the item names the first 100 — the cost of all 353 at depth 16 was outside the item).

## 8. What I am NOT sure about
Whether the fade continues at depth 18+ (unmeasured).

## 9. A better way
My prediction should have normalized the position counts BEFORE banding — the arithmetic error was visible at write time.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long54/stamps.txt
?? forge-combo29/REPORT_deepseek6_long54.md
?? forge-combo29/tests_deepseek6_long54/runs/
?? forge-combo29/tests_deepseek6_long54/table.txt
$ ls forge-combo29/tests_deepseek6_long54/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
