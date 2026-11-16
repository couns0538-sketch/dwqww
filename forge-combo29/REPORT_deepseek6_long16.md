# REPORT — deepseek6, long 16 (recipe R on kimi5's FailHighBlendCheck, its job 12 companion)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long16/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** reproduce kimi5's FailHighBlendCheck counting build (FORGE_FHB_CHECK=1 on top of FailHighBlend): pins, identity rows, its five counter runs compared position by position with its rows and its aggregated FHB counters, plus a sanitizer pass with a planted fault.
**Answer:** R1–R3 met (main-patch sha 8083a257… + check-patch sha 9fedd284…, applied in that order with zero fuzz; pins exact; the check build under S14 with FHB 0 equals my long-1 S14 rows on O 200/200 and G 353/353). R4: **all five runs (FHB 0/1/2/4/7, S14, O, depth 12) equal kimi5's rows on 200 of 200 positions, nodes AND bestmoves, and my aggregated FHB counters equal its counter_sums.txt exactly** — rfp A 1,965,016 (FHB 1); standpat 1,815,929 + qend 734,301 (FHB 2); mainend 1,444,832 (FHB 4); FHB 7: 1,959,912 / 1,777,673 / 711,666 / 1,529,966; L = R = M = 0 everywhere, FHB 0 all zeros. R5: the planted fault IS reported (ASan heap-buffer-overflow, exit 1); the clean sanitizer check build over O under S14 d12: **0 sanitizer lines over 200 positions**.
**How sure:** certain — every number from a committed capture (.fhb, one FHB line per search) aggregated by a committed command and compared against kimi5's committed tables and rows.

## 2. Honesty numbers (check build /tmp/l16_ck/build/forge)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 both shas + apply order + builds | done | R1.txt (sha256sum), build logs | both match; check applies cleanly on top of the main patch |
| R2 pins | done | honesty_*.txt | four exact |
| R3 identity (FHB 0) | done | cmp.txt | O 200/200 (vs kimi5's own json too), G 353/353 vs long-1 |
| R4 rows vs kimi5's five jsons | done | cmp.txt | 200/200 nodes AND bestmove, all five |
| R4 counter sums vs counter_sums.txt | done | my_sums.txt | exact on all five runs, all four places, all four kinds |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, READ of size 4, exit 1 |
| R5 clean sanitizer | done | san/O_s14_fhb0.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md | all three items held |

## 4. Findings
1. **kimi5's FHB counters reproduce to the count on a second machine** — the five runs' A/L/R/M totals are identical, including the L=R=M=0 pattern (no blend ever lands outside [beta, raw] on these sets) and the FHB-0 all-zeros plant-of-absence.
2. **The check build is search-transparent**: its rows equal the plain build's under S14 (R3) and equal kimi5's trees at every FHB value (R4) — the counters observe without disturbing, as claimed.
3. Process disclosure: my first capture run used the wrong harness prefix (the long-13 NSTEPS matcher) and captured nothing; re-run with the FHB matcher before any comparison was claimed. My first bestmove comparison read unstripped fields (spaces) and showed fake 0-of-200 move matches; fixed to stripped comparison — the nodes comparison was unaffected.
4. Suspicions, not proven: none.

## 5. What I read from my colleagues
kimi5's REPORT_kimi5_job12.md (its counter table and its positive control: a planted bit-1 returning beta-1 drives L to A at rfp — its plant, not re-run here; my R5 plant is the sanitizer-class control the recipe asks for); the peer's reports (its job 3 covers the MAIN patch's identity/bits/sanitizers — this report covers the CHECK companion, which that job did not build).
## 6. What I did NOT do
The G-set counter runs (kimi5's counter_sums.txt is O-only; my G run covers the R3 identity). The d16 runs (kimi5's job 12 measured depth 12).

## 7. What I am NOT sure about
Nothing material.

## 8. A better way
None this time.

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long16/stamps.txt
?? forge-combo29/REPORT_deepseek6_long16.md
?? forge-combo29/tests_deepseek6_long16/agg_fhb.py
?? forge-combo29/tests_deepseek6_long16/chkrun.py
?? forge-combo29/tests_deepseek6_long16/cmp.txt
?? forge-combo29/tests_deepseek6_long16/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long16/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long16/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long16/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long16/my_sums.txt
?? forge-combo29/tests_deepseek6_long16/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long16/runs/
?? forge-combo29/tests_deepseek6_long16/san/
$ ls forge-combo29/tests_deepseek6_long16/
agg_fhb.py
chkrun.py
CLAIM.txt
cmp.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
my_sums.txt
plant_evidence.txt
PREDICTION.md
runs
san
stamps.txt
```
