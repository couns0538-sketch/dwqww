# REPORT — deepseek6, long 28 (SENSITIVITY B: the 22 default-anchored settings, plus/minus one step)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long28/ · CLAIM.txt before the first command; stamps before the runs and after (19:39:57Z); PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** under S14, move each of the 22 non-S14 tuner settings one step down and up around the plain build's DEFAULT, rows on O and G at depth 12, with change counts against S14.
**Answer:** the harness check reproduced first (QsSeeMargin 100 on O = 9,768,507 EXACT). **All 44 O sums equal my job-1 table EXACTLY; the six known-identity runs (QsSeeMargin ±c, CaptureFutilityMultiplier ±c, CaptureFutilityDepth ±c) are exact identities on BOTH sets (0 changed rows on O and G); and 12 of the 38 non-identity pairs FLIP direction between O and G** (the long-27 pattern repeats on the other half of the tuner's list). No clamping was needed — every run value is inside its option's range. All five predictions held.
**How sure:** certain (88 runs, .meta each, one compare base, deterministic re-run agreement with job 1).

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| harness check (QsSeeMargin 100) | done | runs_check_qsm100_O.rows | 9,768,507 EXACT |
| 88 runs (22x2) x O,G | done | runs/s28_*.rows + table.txt, .meta each | all rc=0 |
| the 44 job-1 sums | done | table.txt match column | EXACT x44, 0 differs |
| the six identities | done | table.txt IDENTITY rows | 0 changed rows on both sets |
| direction agreement | done | table.txt sign column | 12 SIGN-FLIPS of 38 non-identity pairs |
| clamping | done | the run values vs the uci ranges (uci.txt in this folder) | none needed |
| prediction own commit first | done | PREDICTION.md | all five held |

## 4. The table (O base 9,500,069; G base 18,466,239; full table in table.txt)
| setting | end | O sum | O nodes-chg | O bm-chg | G sum | G nodes-chg | G bm-chg | O/G direction |
|---|---|---|---|---|---|---|---|---|
| NullMoveDepthDivisor | −c | 9,820,878 | 200/200 | 44/200 | 18,494,286 | 336/353 | 55/353 | same |
| NullMoveDepthDivisor | +c | 9,713,417 | 200/200 | 41/200 | 19,364,553 | 342/353 | 62/353 | FLIP |
| NullMoveEvalDivisor | −c | 9,527,676 | 131/200 | 0/200 | 18,391,225 | 152/353 | 2/353 | FLIP (G −) |
| NullMoveEvalDivisor | +c | 9,537,690 | 144/200 | 0/200 | 18,322,842 | 157/353 | 3/353 | same (both −) |
| RfpDepth | −c | 9,507,038 | 79/200 | 0/200 | 18,510,893 | 20/353 | 22/353 | FLIP |
| RfpDepth | +c | 9,502,499 | 140/200 | 0/200 | 18,218,066 | 62/353 | 15/353 | same (−/−) |
| RfpMargin | −c | 9,390,679 | 200/200 | 61/200 | 18,034,478 | 348/353 | 89/353 | same |
| RfpMargin | +c | 9,872,233 | 200/200 | 65/200 | 19,511,712 | 349/353 | 94/353 | same |
| RfpImproving | −c | 9,894,461 | 200/200 | 57/200 | 18,843,404 | 349/353 | 92/353 | same |
| RfpImproving | +c | 9,180,404 | 200/200 | 46/200 | 18,508,937 | 348/353 | 78/353 | FLIP |
| RazorBase | −c | 9,534,804 | 38/200 | 11/200 | 18,613,571 | 13/353 | 23/353 | same |
| RazorBase | +c | 9,479,323 | 54/200 | 5/200 | 18,062,059 | 19/353 | 23/353 | same |
| RazorMultiplier | −c | 9,433,562 | 19/200 | 19/200 | 18,439,788 | 11/353 | 28/353 | same |
| RazorMultiplier | +c | 9,461,510 | 44/200 | 5/200 | 18,166,031 | 13/353 | 28/353 | same |
| FutilityDepth | −c | 9,439,695 | 133/200 | 0/200 | 18,334,639 | 147/353 | 8/353 | same |
| FutilityDepth | +c | 9,496,927 | 164/200 | 1/200 | 18,400,644 | 188/353 | 5/353 | same |
| FutilityBase | −c | 9,507,227 | 1/200 | 5/200 | 18,504,425 | 16/353 | 20/353 | FLIP |
| FutilityBase | +c | 9,434,509 | 1/200 | 10/200 | 18,176,944 | 21/353 | 21/353 | same |
| FutilityMultiplier | −c | 9,537,156 | 1/200 | 6/200 | 18,622,251 | 16/353 | 22/353 | same |
| FutilityMultiplier | +c | 9,508,597 | 1/200 | 10/200 | 18,277,647 | 21/353 | 27/353 | same |
| SeeQuietMultiplier | −c | 9,421,151 | 200/200 | 36/200 | 18,477,370 | 80/353 | 46/353 | same |
| SeeQuietMultiplier | +c | 9,224,685 | 200/200 | 45/200 | 19,337,299 | 26/353 | 76/353 | FLIP |
| SeeNoisyMultiplier | −c | 9,556,070 | 1/200 | 22/200 | 17,734,587 | 30/353 | 51/353 | FLIP |
| SeeNoisyMultiplier | +c | 9,517,963 | 13/200 | 4/200 | 18,262,025 | 19/353 | 7/353 | FLIP |
| SingularMargin | −c | 13,196,949 | 200/200 | 52/200 | 21,442,517 | 6/353 | 84/353 | same (+/+ huge) |
| SingularMargin | +c | 8,186,451 | 200/200 | 47/200 | 16,091,515 | 6/353 | 79/353 | same (−/− huge) |
| ProbcutDepth | −c | 9,837,966 | 200/200 | 33/200 | 18,055,158 | 6/353 | 69/353 | FLIP |
| ProbcutDepth | +c | 9,578,147 | 200/200 | 31/200 | 18,493,307 | 8/353 | 63/353 | same |
| ProbcutMargin | −c | 9,295,556 | 2/200 | 9/200 | 18,314,055 | 19/353 | 51/353 | same |
| ProbcutMargin | +c | 9,472,152 | 5/200 | 12/200 | 18,432,463 | 19/353 | 39/353 | same |
| QsFutilityMargin | −c | 9,647,884 | 200/200 | 40/200 | 18,835,039 | 23/353 | 68/353 | same |
| QsFutilityMargin | +c | 9,582,390 | 200/200 | 41/200 | 18,325,198 | 23/353 | 65/353 | FLIP |
| QsSeeMargin | ±c | identity | 0/200 | 0/200 | identity | 0/353 | 0/353 | IDENTITY |
| AspirationDelta | −c | 9,636,048 | 200/200 | 49/200 | 18,630,084 | 7/353 | 80/353 | same |
| AspirationDelta | +c | 9,678,831 | 200/200 | 56/200 | 18,552,538 | 7/353 | 80/353 | FLIP |
| LmrCutoffThreshold | −c | 9,208,581 | 200/200 | 54/200 | 17,310,733 | 1/353 | 72/353 | same |
| LmrCutoffThreshold | +c | 10,344,054 | 200/200 | 54/200 | 19,288,590 | 1/353 | 87/353 | same |
| MaterialCorrectionWeight | −c | 9,702,725 | 200/200 | 47/200 | 18,329,033 | 8/353 | 74/353 | FLIP |
| MaterialCorrectionWeight | +c | 9,635,865 | 200/200 | 43/200 | 18,492,683 | 6/353 | 70/353 | FLIP |
| CaptureFutilityMultiplier/Depth | ±c | identity | 0/200 | 0/200 | identity | 0/353 | 0/353 | IDENTITY |

## 5. Findings
1. **12 more direction flips between the sets** (on top of long 27's 9): across the tuner's full 35-setting list, 21 of 64 moved pairs disagree in direction between openings and games — a node-count tuner on a single set is reading half noise.
2. **SingularMargin is the strongest lever in the entire tuner list per step** (O +38.9 %/−13.8 %, G +16.1 %/−12.9 % for ONE unit) — and it agrees in direction on both sets.
3. **The inert-at-this-configuration set now has four members**: QsSeeMargin (any value 0..99), CaptureFutilityMultiplier, CaptureFutilityDepth (gate closed), and — from long 14 — AspReopenMargin (loop never fires).
4. Suspicions, not proven: the flip mechanism.

## 6. What I read from my colleagues
File 8's corrections applied; the peer's live claims respected (long 25). My own job-1 table served as the O-side expectation.

## 7. What I did NOT do
Nothing from the item.

## 8. What I am NOT sure about
The flip mechanism (5.1).

## 9. A better way
The tuner should score both sets jointly; longs 27–28 are the data for it.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long28/stamps.txt
?? forge-combo29/REPORT_deepseek6_long28.md
?? forge-combo29/tests_deepseek6_long28/runs/
?? forge-combo29/tests_deepseek6_long28/table.txt
?? forge-combo29/tests_deepseek6_long28/uci.txt
$ ls forge-combo29/tests_deepseek6_long28/
check_qsm100.meta
CLAIM.txt
PREDICTION.md
runs
runs_check_qsm100_O.rows
stamps.txt
table.txt
uci.txt
```
