# REPORT — deepseek6, long 47 (the root restriction: plain vs searchmoves-all vs MultiPV)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long47/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** under S14 at depth 12 on the first 50 of O: (a) plain, (b) `go depth 12 searchmoves <every legal move>`, (c) MultiPV 1 explicit, (d) MultiPV 2 — is (b) identical to (a) node for node; if not, how many positions and which direction.
**Answer:** **(b) is NOT identical: it differs from (a) on 50 of 50 positions, and it is SMALLER — (b) 1,483,521 against (a) 2,150,681 (−31.0 %), bigger on only 8 of the 50.** My prediction said the opposite direction (the IIR tax making the tree bigger) and is KILLED — the mechanism is the one my prior run's long-6 data already contained: a restricted root stores no TT entry, so from the second iteration the root has no hash move, the internal iterative reduction fires AT THE ROOT, and the root is searched one ply shallower — a SMALLER tree. (c) MultiPV 1 explicit is IDENTICAL to (a) on all 50 rows (prediction 1 held). (d) MultiPV 2 = 3,893,160 = 1.810× (a) (inside my 1.8–2.2 band ✓).
**How sure:** certain of the four runs (.meta each; the searchmoves lists built from python-chess per position).

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| the searchmoves lists (python-chess) | done | /tmp/o50_sm.txt (format fen \| moves) | 50 lines |
| the four runs | done | runs/a_plain.rows, b_searchmoves.rows, c_mpv1.rows, d_mpv2.rows | all rc=0, .meta each |
| the four-way comparison | done | cmp.txt | (b) differs 50/50, smaller on 42; (c) identical; (d) 1.810x |
| prediction own commit first | done | PREDICTION.md | 1, 3 held; 2 killed (the direction), its 50-of-50 part held |

## 4. Findings
1. **The restricted root is searched one ply shallower** — the measured −31 % tree shrink under searchmoves-all is the IIR-at-root effect; my prior run's long-6 patch (IirRootExclude) measured the same mechanism from the other side (+55 % when the root is EXCLUDED from IIR).
2. **The direction of my prediction was wrong because I mis-stated my own prior data** — the long-6 numbers contained the answer; a prediction should be checked against the session's own committed reports before it is committed.
3. **MultiPV 1 explicit == plain exactly** — the option's plumbing is transparent at its default value.
4. Suspicions, not proven: none.

## 6. What I read from my colleagues
Nothing new this item (the peer on long 34/43; file 13's corrections applied at long 46).

## 7. What I did NOT do
The IirRootExclude patch re-test at this setting (my prior run's long-6 covers it; the item asks for the plain behavior only).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
Before committing a prediction, grep my own branch's prior reports for the same mechanism — my long-6 had the direction all along.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long47/stamps.txt
?? forge-combo29/REPORT_deepseek6_long47.md
?? forge-combo29/tests_deepseek6_long47/cmp.txt
?? forge-combo29/tests_deepseek6_long47/runs/
?? forge-combo29/tests_deepseek6_long47/smrun.py
$ ls forge-combo29/tests_deepseek6_long47/
CLAIM.txt
cmp.txt
PREDICTION.md
runs
smrun.py
stamps.txt
```
