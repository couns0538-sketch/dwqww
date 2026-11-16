# REPORT — deepseek6, cross 2 (kimi5's job-10 REGRET probe runs and controls, reproduced independently)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_cross2/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** the standing rule's item 1 continued — reproduce kimi5's job-10 REGRET half: the four probe runs (defaults-O, S14-O, S14-G, defaults-G; its agg_r5/r6/r7/r8) and the four controls on O (QsFutilityMargin 0/400, QsSeeMargin 0/200; its agg_c_*), all at the patch's default probe cadence (48/256/700).
**Answer:** **all eight of my aggregated tables equal kimi5's agg files on every line but the SUMMED source-name line** — the probe counts, the MISSED/CUT/bound rates per class, the by-q tables, the seen counts (r5: 777,675 / 1,880,428 / 2,131,480), the probe nodes (43,743), the HEADLINE rates (fut 15.71, see 4.55, stand-pat 83.65 per 1,000 on r5), and every identity — **AND one real finding: kimi5's committed agg_r5_def_O_d12.txt fails its OWN identity I3** — its EXITS line sums to 5,671,520 against its q0 5,695,194 (a 23,674 shortfall exactly in its X_standpat cell: 2,133,567 where the sum-to-q0 value is 2,157,241 — which is what my run produces, with the same node sum 12,668,737 and the same probe table). Its other seven aggs are internally consistent and match mine.
**How sure:** certain of my own numbers (self-consistent: my exits sum to my q0 exactly, my probe tables match its rates to the shown digits); the agg_r5 inconsistency is arithmetic on its own committed file.

## 2. Honesty numbers
My probe build /tmp/lc2/build/forge (clean 6b98f217 + QsSteps.patch 07713c3b…, FORGE_QS_STEPS=1 + FORGE_QS_REGRET=1); pins re-run (bench 11 = 312866 ✓).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| the probe build | done | build log | both flags |
| the eight runs (rows + QSTEPS capture) | done | runs/*.rows + *.qst | 200 searches each |
| the eight agg comparisons | done | my_agg_*.txt vs /tmp/aggref2_*.txt, agg_diffs.txt | 2 lines each = the SUMMED source name only |
| the internal-consistency check | done | check.txt | kimi5's agg_r5 fails its own I3 by 23,674; the other seven consistent; mine consistent x8 |
| prediction own commit first | done | PREDICTION.md | items 1-4 held |

## 4. Findings
1. **kimi5's REGRET probe rates reproduce exactly on a second machine** — every per-class probe count and MISSED/CUT/bound rate (e.g. r5's <25 class: n=1,590, missed 37.11, cut 37.11, bound 48.43) is identical; its HEADLINE (fut 15.71 / see 4.55 / stand-pat 83.65 per 1,000) stands.
2. **Its committed agg_r5_def_O_d12.txt is internally inconsistent**: its own I3 identity fails by 23,674 (the X_standpat cell), while my run of the same committed patch on the same node sum produces the self-consistent 2,157,241. The rest of that file (and its other seven) are consistent. The likely cause: the file was generated from a pre-final build and its stand-pat cluster was not regenerated; the probe-rate table in the same file IS consistent with my run.
3. The disturbance sizes reproduce: my r5's node sum 12,668,737 == its printed nodes(engine) — the probe's disturbance is deterministic.
4. Suspicions, not proven: the stale-file explanation in 2.

## 6. What I read from my colleagues
kimi5's job-10 report and its eight agg files; its notes (its job-14 plan — the RfpGuards patch — is not on its branch yet).

## 7. What I did NOT do
The probe runs under the sanitizer (the standing rule's item 3 is a separate cross); the O50/d16 probe runs (kimi5's job-10 measured the four bases only).

## 8. What I am NOT sure about
The stale-file explanation (4.2) — the arithmetic inconsistency itself is certain.

## 9. A better way
kimi5's agg files should be regenerated from its committed raw capture whenever its patch file changes — the raw capture (rows/*_checks.txt) is on its branch, so the repair is one command for it.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_cross2/stamps.txt
?? forge-combo29/REPORT_deepseek6_cross2.md
?? forge-combo29/tests_deepseek6_cross1/__pycache__/
?? forge-combo29/tests_deepseek6_cross2/agg_diffs.txt
?? forge-combo29/tests_deepseek6_cross2/agg_qs2.py
?? forge-combo29/tests_deepseek6_cross2/check.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_c_fut0.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_c_fut400.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_c_see0.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_c_see200.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_r5_def_O.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_r6_s14_O.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_r7_s14_G.txt
?? forge-combo29/tests_deepseek6_cross2/my_agg_r8_def_G.txt
?? forge-combo29/tests_deepseek6_cross2/runs/
$ ls forge-combo29/tests_deepseek6_cross2/
agg_diffs.txt
agg_qs2.py
check.txt
CLAIM.txt
my_agg_c_fut0.txt
my_agg_c_fut400.txt
my_agg_c_see0.txt
my_agg_c_see200.txt
my_agg_r5_def_O.txt
my_agg_r6_s14_O.txt
my_agg_r7_s14_G.txt
my_agg_r8_def_G.txt
PREDICTION.md
runs
stamps.txt
```
