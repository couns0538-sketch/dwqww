# REPORT — deepseek6, long 29 (SENSITIVITY C: depth 14 for the sub-0.5-percent movers)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long29/ · CLAIM.txt before the first command; stamps before the runs and after (19:45:46Z); PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** depth 14 on O for every long-27/28 setting whose O tree moved less than 0.5 % at depth 12 — alive deeper or not.
**Answer:** the S14 anchor is EXACT (21,812,100). **The six identity runs stay exact identities at depth 14 (0 changed rows each); all 19 qualifying movers (my prediction said 18 — the list recount below) stay ALIVE at depth 14, and 15 of the 19 have grown past the 0.5 % band** — the small depth-12 effects mostly GROW with depth (e.g. RazorMultiplier +c: 0.35 % → 3.49 %; LmrNoisyDivisor +c: 0.20 % → 3.46 %; HistoryBonusLinear +c: 0.26 % → 0.90 %), while a few shrink relatively (FutilityDepth +c: 0.03 % → 0.001 % — 63 nodes).
**How sure:** certain (26 runs, .meta each; the anchor exact).

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim + prediction | done | CLAIM.txt, PREDICTION.md | — |
| the anchor run | done | table.txt first line | 21,812,100 EXACT |
| the six identity runs at d14 | done | table.txt IDENTITY rows | all exact (0 changed rows) |
| the 19 mover runs at d14 | done | table.txt | all alive; 15 over the band |
| prediction scorecard | done | table.txt | 1, 2 held; 3 held (19/19 alive; my list count said 18 — recount disclosed); 4 held (15 in [8, 16]) |

## 4. The table (d14 sums; ratio vs 21,812,100; full table in table.txt)
| setting (end) | d12 ratio | d14 sum | d14 ratio | nodes-chg | verdict |
|---|---|---|---|---|---|
| LmrNoisyDivisor (+c) | 1.0020 | 22,566,695 | 1.0346 | 200/200 | grew past the band |
| LmpBase (−c) | 1.0025 | 21,657,484 | 0.9929 | 200/200 | grew |
| HistoryPruneMultiplier (−c) | 1.0032 | 21,677,254 | 0.9938 | 196/200 | grew |
| HistoryBonusQuadratic (+c) | 1.0003 | 21,752,647 | 0.9973 | 200/200 | stayed small |
| HistoryBonusLinear (+c) | 1.0026 | 22,009,311 | 1.0090 | 200/200 | grew |
| HistoryBonusMax (−c) | 1.0023 | 22,312,557 | 1.0229 | 200/200 | grew |
| NullMoveEvalDivisor (−c) | 1.0029 | 21,995,696 | 1.0084 | 159/200 | grew |
| NullMoveEvalDivisor (+c) | 1.0040 | 21,748,143 | 0.9971 | 139/200 | stayed small |
| RfpDepth (−c) | 1.0007 | 21,613,309 | 0.9909 | 169/200 | grew |
| RfpDepth (+c) | 1.0026 | 21,619,378 | 0.9912 | 134/200 | grew |
| RazorBase (−c) | 1.0037 | 21,556,447 | 0.9883 | 192/200 | grew |
| RazorMultiplier (−c) | 0.9970 | 21,992,246 | 1.0083 | 193/200 | grew |
| RazorMultiplier (+c) | 0.9965 | 22,573,032 | 1.0349 | 187/200 | grew |
| FutilityDepth (+c) | 0.9997 | 21,812,229 | 1.0000 | 63/200 | nearly vanished |
| FutilityBase (−c) | 1.0008 | 22,029,024 | 1.0099 | 200/200 | grew |
| FutilityMultiplier (−c) | 1.0039 | 21,917,032 | 1.0048 | 200/200 | stayed small |
| FutilityMultiplier (+c) | 1.0009 | 22,114,486 | 1.0139 | 200/200 | grew |
| SeeNoisyMultiplier (+c) | 1.0019 | 22,124,256 | 1.0143 | 196/200 | grew |
| ProbcutMargin (+c) | 0.9971 | 21,925,606 | 1.0052 | 200/200 | grew |
| QsSeeMargin (±c) | identity | 21,812,100 | 1.0000 | 0/200 | identity at d14 too |
| CaptureFutilityMultiplier/Depth (±c) | identity | 21,812,100 | 1.0000 | 0/200 | identity at d14 too |

## 5. Findings
1. **"Small at depth 12" does not mean "small at depth 14"**: 15 of the 19 movers cross the 0.5 % band by depth 14 (the median ratio distance roughly quadruples). A tuner pruning its list by depth-12 sensitivity would discard settings that matter two plies deeper.
2. **The exceptions are informative**: FutilityDepth +c nearly vanishes (63 nodes at d14 — its depth-12 effect was already a boundary artifact); NullMoveEvalDivisor's node churn stays partial (139–159 of 200) — its effect is position-dependent, not global.
3. The identity set is depth-stable (QsSeeMargin's 0..99 band and the closed capture-futility gate hold at depth 14 exactly as at 12).
4. Suspicions, not proven: the growth mechanism (deeper searches amplify small margin changes).

## 6. What I read from my colleagues
Nothing new this item (the 4-hour colleague read is due; the peer's live long-25 claim respected).

## 7. What I did NOT do
G-set depth-14 runs (the item names O only); the depth-14 runs of the OVER-band settings (out of scope).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The d12 sensitivity list should be re-derived at the depth the tuner actually searches (this item is that warning, quantified).

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long29/stamps.txt
?? forge-combo29/REPORT_deepseek6_long29.md
?? forge-combo29/tests_deepseek6_long29/runs/
?? forge-combo29/tests_deepseek6_long29/table.txt
$ ls forge-combo29/tests_deepseek6_long29/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
