# REPORT — deepseek6, long 27 (SENSITIVITY A: the S14 settings at plus/minus one step, O and G)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long27/ · CLAIM.txt before the first command; stamps at the build (none needed — the plain build), before the runs (prediction commit line), after the runs (19:34:37Z); PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** under S14, move each of the 13 numeric S14 settings one step down and up (and NonPawnCorrection to false), rows on O and G at depth 12, with the node/bestmove change counts against S14.
**Answer:** the harness check reproduced first (LmrHistoryDivisor 5644 on O = 9,512,627 EXACT). **All 26 job-1-overlapping O sums equal my job-1 table EXACTLY** (deterministic re-run confirmed). **NonPawnCorrection false changes both sets (O 9,738,053 = +2.51 %, G 18,559,891 = +0.51 %).** The surprise: **prediction 3 KILLED — 9 of the 26 O/G direction pairs FLIP** (LmrNoisyBase −c, LmrNoisyDivisor both ends, LmrHistoryDivisor +c, NullMoveBase +c, LmpBase −c, HistoryPruneMultiplier both ends, HistoryBonusMax both ends): the openings tree and the games tree move in OPPOSITE directions for a third of the one-step moves.
**How sure:** certain of the numbers (54 runs, .meta each, one compare base); the direction disagreement is measured, its mechanism untraced.

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| harness check (5644) | done | /tmp/l27_check.rows (copied to runs/ as check_5644_O.rows) | 9,512,627 EXACT |
| 54 runs (13x2 + 1) x O,G | done | runs/s27_*.rows + table.txt, .meta each | all rc=0 |
| the 26 job-1 sums | done | table.txt match column | EXACT x26 |
| NonPawnCorrection false | done | table.txt last rows | different on both sets |
| direction agreement | done | table.txt sign column | 9 SIGN-FLIPS of 26 — prediction 3 killed |
| prediction own commit first | done | PREDICTION.md | 1, 2, 4 held; 3 killed |

## 4. The table (full, from table.txt; O base 9,500,069, G base 18,466,239)
| setting | end | O sum | O nodes-chg | O bm-chg | G sum | G nodes-chg | G bm-chg | O/G direction |
|---|---|---|---|---|---|---|---|---|
| LmrQuietBase | −c | 10,081,111 | 200/200 | 55/200 | 19,725,735 | 352/353 | 86/353 | same (+/+) |
| LmrQuietBase | +c | 9,314,278 | 200/200 | 49/200 | 17,427,644 | 352/353 | 85/353 | same (−/−) |
| LmrQuietDivisor | −c | 9,035,329 | 200/200 | 52/200 | 17,160,467 | 353/353 | 75/353 | same |
| LmrQuietDivisor | +c | 10,708,626 | 200/200 | 50/200 | 19,450,187 | 352/353 | 91/353 | same |
| LmrNoisyBase | −c | 9,627,099 | 161/200 | 9/200 | 18,362,777 | 281/353 | 16/353 | FLIP (+/−) |
| LmrNoisyBase | +c | 9,615,327 | 147/200 | 6/200 | 18,614,238 | 293/353 | 15/353 | same |
| LmrNoisyDivisor | −c | 9,671,551 | 159/200 | 6/200 | 18,063,353 | 298/353 | 19/353 | FLIP |
| LmrNoisyDivisor | +c | 9,519,342 | 199/200 | 16/200 | 18,121,025 | 294/353 | 34/353 | FLIP |
| LmrHistoryDivisor | −c | 9,632,276 | 200/200 | 42/200 | 18,469,150 | 349/353 | 73/353 | same (barely) |
| LmrHistoryDivisor | +c | 9,746,633 | 200/200 | 46/200 | 18,080,730 | 347/353 | 66/353 | FLIP |
| NullMoveBase | −c | 9,912,856 | 200/200 | 38/200 | 19,045,006 | 342/353 | 59/353 | same |
| NullMoveBase | +c | 9,906,893 | 200/200 | 21/200 | 18,414,218 | 336/353 | 49/353 | FLIP |
| LmpBase | −c | 9,523,884 | 200/200 | 56/200 | 17,952,112 | 351/353 | 99/353 | FLIP |
| LmpBase | +c | 9,828,280 | 200/200 | 50/200 | 18,525,529 | 351/353 | 83/353 | same |
| HistoryPruneMultiplier | −c | 9,530,219 | 165/200 | 8/200 | 18,303,533 | 298/353 | 27/353 | FLIP |
| HistoryPruneMultiplier | +c | 9,579,620 | 155/200 | 9/200 | 18,176,819 | 288/353 | 29/353 | FLIP |
| HistoryBonusQuadratic | −c | 9,358,128 | 200/200 | 46/200 | 18,088,051 | 348/353 | 86/353 | same |
| HistoryBonusQuadratic | +c | 9,502,882 | 200/200 | 35/200 | 18,530,826 | 351/353 | 89/353 | same |
| HistoryBonusLinear | −c | 9,674,952 | 200/200 | 50/200 | 18,500,349 | 348/353 | 77/353 | same |
| HistoryBonusLinear | +c | 9,525,119 | 200/200 | 48/200 | 18,481,629 | 350/353 | 79/353 | same |
| HistoryBonusMax | −c | 9,522,214 | 190/200 | 18/200 | 18,155,655 | 332/353 | 49/353 | FLIP |
| HistoryBonusMax | +c | 9,745,469 | 187/200 | 22/200 | 18,133,398 | 338/353 | 43/353 | FLIP |
| SingularDepth | −c | 9,732,613 | 200/200 | 56/200 | 21,159,646 | 349/353 | 77/353 | same (+/+ strong) |
| SingularDepth | +c | 9,163,603 | 200/200 | 54/200 | 16,788,624 | 349/353 | 87/353 | same (−/− strong) |
| IirDepth | −c | 10,189,982 | 200/200 | 53/200 | 18,543,479 | 352/353 | 92/353 | same |
| IirDepth | +c | 10,450,178 | 200/200 | 59/200 | 19,499,403 | 351/353 | 85/353 | same |
| NonPawnCorrection | false | 9,738,053 | 200/200 | 52/200 | 18,559,891 | 347/353 | 80/353 | same (+/+) |

## 5. Findings
1. **A third of the one-step moves disagree in DIRECTION between the openings and the games tree** (9 of 26). The flips cluster in the noisy/history terms (LmrNoisy*, HistoryPruneMultiplier, HistoryBonusMax) plus NullMoveBase +c and LmpBase −c. A node-count tuner reading only openings would push several settings the wrong way for game positions.
2. **SingularDepth is the strongest G-mover per step** (±c moves G by +14.6 % / −9.1 %) — far beyond its O effect (+2.5 % / −3.5 %).
3. **NonPawnCorrection false costs +2.51 % nodes on O and +0.51 % on G** — the pawn-only correction is a real, set-dependent lever.
4. The bestmove churn stays modest everywhere (6–99 of 200/353); the biggest bestmove movers on G are LmpBase −c (99) and IirDepth ±c (92/85).
5. Suspicions, not proven: the flip mechanism (the two sets' different depth profiles meet the same term change differently).

## 6. What I read from my colleagues
File 8's corrections applied (stamps per stage; claims respected — long 25 is the peer's live claim, long 23 its finished report). My job-1 table supplied the O expectations (my own earlier measurement — the re-run's exactness is the point).

## 7. What I did NOT do
Nothing from the item.

## 8. What I am NOT sure about
The flip mechanism (5.1).

## 9. A better way
The tuner should weigh O and G jointly; this table is the data for that weighting.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long27/stamps.txt
?? forge-combo29/REPORT_deepseek6_long27.md
?? forge-combo29/tests_deepseek6_long27/runs/
?? forge-combo29/tests_deepseek6_long27/table.txt
$ ls forge-combo29/tests_deepseek6_long27/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
