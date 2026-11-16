# REPORT — deepseek6, cross 1 (kimi5's job-10 quiescence counters, reproduced independently)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_cross1/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs. Scope: the four STEPS runs (the FORGE_QS_STEPS=1 build); the REGRET probe runs and their missed-rate tables are left for a later cross (stated cut).

## 1. Three lines
**Asked:** the standing rule's item 1 — kimi5's job-10 report (the quiescence-search counters) had been reproduced by nobody but kimi5; reproduce its four measured runs' aggregated tables on a clean 6b98f217 build of its patch.
**Answer:** **my four aggregated tables equal kimi5's agg_k1_def_O / agg_k2_s14_O / agg_k3_s14_G / agg_k4_def_G on EVERY line but one** — the sole difference in each file is the SUMMED line's source-file name (my capture file vs its rows path; by design). **The counts are identical to the unit**: q0 5,643,723 (O defaults) and 4,629,887 (O S14) with the q-class/pv/in-check splits, the five call-site rows, the seven exit classes with the X_tt bound split (5741/308066/190396), the stand-pat margin classes, the S_tt counts, the moves rows and their I4 partition (legal = searched + futility + SEE), the P_fut/P_see/CUT splits, and all six identity flags 0 everywhere. The counter build's rows equal the plain rows on every position of all four runs. ALL FOUR PREDICTIONS HELD.
**How sure:** certain — the comparison is a line diff of my emitter's output against kimi5's committed agg files; the numbers agree to the unit across ~11 M counted events.

## 2. Honesty numbers
My flag build /tmp/lc1/build/forge (clean 6b98f217 + QsSteps.patch 07713c3b…, FORGE_QS_STEPS=1): bench pins inherited from the same source (the plain tree) — re-run: bench 11 = 312866 ✓ (in the stamps).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the flag build | done | build log | built with -DFORGE_QS_STEPS=1 |
| the four runs (rows + QSTEPS capture) | done | runs/*.rows + *.qst | 200/353 searches each |
| the row identities | done | rowscmp.txt | all four 200/200 or 353/353, nodes and moves |
| the four agg comparisons | done | my_agg_*.txt vs /tmp/aggref_*.txt | identical but the SUMMED source name |
| prediction own commit first | done | PREDICTION.md | all four held |

## 4. Findings
1. **kimi5's job-10 counters reproduce to the unit on a second machine** — the qsearch share (44.89 % of O-defaults nodes; 48.74 % under S14 — wait, my k2's share: q0 4,629,887 / 9,500,069 = 48.74 % ✓ the report's number), the exit-class distribution, the stand-pat margin histogram, the moves partition and the fail-high cut-index histogram all match exactly.
2. The aggregator took several iterations to mirror the format (the reg-section label reuse, the q-range slips, the K2 key parsing); the final diff is 2 lines per file = the source-name line only.
3. Suspicions, not proven: none.

## 6. What I read from my colleagues
kimi5's job-10 report and its agg files (the comparison targets); its notes (the plateau-edges advice — already applied in my long 39).

## 7. What I did NOT do
The REGRET probe runs (scope cut stated); the sanitizer pass (that is the standing rule's item 3 — a separate cross).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
None; the emitter now mirrors the format exactly and is reusable for any future QSTEPS reproduction.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_cross1/stamps.txt
?? forge-combo29/REPORT_deepseek6_cross1.md
?? forge-combo29/tests_deepseek6_cross1/agg_qs.py
?? forge-combo29/tests_deepseek6_cross1/chkrun.py
?? forge-combo29/tests_deepseek6_cross1/my_agg_k1.txt
?? forge-combo29/tests_deepseek6_cross1/my_agg_k1_def_O.txt
?? forge-combo29/tests_deepseek6_cross1/my_agg_k2_s14_O.txt
?? forge-combo29/tests_deepseek6_cross1/my_agg_k3_s14_G.txt
?? forge-combo29/tests_deepseek6_cross1/my_agg_k4_def_G.txt
?? forge-combo29/tests_deepseek6_cross1/rowscmp.txt
?? forge-combo29/tests_deepseek6_cross1/runs/
$ ls forge-combo29/tests_deepseek6_cross1/
agg_qs.py
chkrun.py
CLAIM.txt
my_agg_k1_def_O.txt
my_agg_k1.txt
my_agg_k2_s14_O.txt
my_agg_k3_s14_G.txt
my_agg_k4_def_G.txt
PREDICTION.md
rowscmp.txt
runs
stamps.txt
```
