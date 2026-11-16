# REPORT — deepseek6, long 48 (the Hash sweep and the carried-TT run)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long48/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** Hash 1, 4, 16, 64, 256 MB under S14 at depth 12 on O (rows each; 16 must equal 9,500,069), then the same 50 positions searched in ONE process without ucinewgame (Hash 16) against the fresh-process rows.
**Answer:** Hash 16/64/256 are EXACTLY 9,500,069 (0 changed rows); **Hash 4 differs on only 10 positions (sum −0.000075 %)**; **Hash 1 changes 140 positions and its sum is SMALLER (−0.22 %) — my monotone prediction is KILLED** (the thrashing table does not grow the tree, it shrinks it slightly). **The no-ucinewgame run is +1.50 % BIGGER than the fresh rows (49 of 50 positions changed, 14 best moves) — my "smaller" prediction is KILLED**: the carried entries from previous positions hurt, they do not help.
**How sure:** certain (seven runs, .meta each; the twin comparisons row-for-row).

## 2. Honesty numbers
The plain build (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| the five Hash runs (O, 200) | done | runs/hash*_O.rows + table.txt | 16/64/256 EXACT; 4 nearly; 1 smaller |
| the fresh 50-position rows | done | runs/fresh50.rows | 2,150,681 |
| the no-ucinewgame rows | done | runs/nonu50.rows (nounrows harness /tmp/l48_nonu.py) | 2,182,852 (+1.50 %) |
| prediction own commit first | done | PREDICTION.md | 1, 3 held; 2, 4 killed |

## 4. The table
| Hash | sum | positions changed | best moves changed | vs 9,500,069 |
|---|---|---|---|---|
| 1 | 9,479,358 | 140/200 | 4/200 | −0.22 % |
| 4 | 9,499,998 | 10/200 | 0/200 | −0.0001 % |
| 16 | 9,500,069 | 0/200 | 0/200 | EXACT |
| 64 | 9,500,069 | 0/200 | 0/200 | EXACT |
| 256 | 9,500,069 | 0/200 | 0/200 | EXACT |
| fresh50 | 2,150,681 | — | — | — |
| nonu50 | 2,182,852 | 49/50 vs fresh | 14/50 | +1.50 % |

## 5. Findings
1. **The hash-size response is non-monotone at the small end**: Hash 1's tree is SMALLER than Hash 16's despite 140 changed positions — the thrashing table changes the search everywhere but does not enlarge it; my "forgetting means re-searching means bigger" reasoning was wrong in sign.
2. **The TT carry-over between positions is harmful at depth 12** (+1.5 % nodes, 14 best moves): entries searched under other positions' paths mislead the next search. The engine's own protocol (ucinewgame between positions) is the right one, measured.
3. **The working set at depth 12 fits in 16 MB** (Hash 4 already differs on only 10 positions by a handful of nodes; 16/64/256 identical).
4. Suspicions, not proven: the sign of finding 1's mechanism.

## 6. What I read from my colleagues
Nothing new this item.

## 7. What I did NOT do
Hash values between 4 and 16; the G set (the item names O).

## 8. What I am NOT sure about
Finding 1's mechanism.

## 9. A better way
None.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long48/stamps.txt
?? forge-combo29/REPORT_deepseek6_long48.md
?? forge-combo29/tests_deepseek6_long48/runs/
?? forge-combo29/tests_deepseek6_long48/table.txt
$ ls forge-combo29/tests_deepseek6_long48/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
