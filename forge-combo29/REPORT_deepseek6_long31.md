# REPORT — deepseek6, long 31 (recipe R on LmrFine ALONE; R4 = kimi5's job-11 runs)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long31/ · CLAIM.txt before the first command; stamps per stage; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** recipe R on LmrFine.patch.txt alone (my longs 19/21 used it inside bundles), with R4 = ALL FOURTEEN of kimi5's job-11 runs compared position by position with its rows jsons.
**Answer:** **R1–R4 all met: sha f7bf3f43… verified; pins exact; the uci list shows the ten options with kimi5's defaults; ALL FOURTEEN runs (i1 defaults, i2 S14, i3 fine-switch identity, i4 S14+fine identity — each on O and G — plus c1 tt1025 (13,036,988), c2 tt1023 (9,500,069), t1 (10,170,054 / 19,269,858), t2 (11,915,365 / 22,952,032)) equal kimi5's rows on 200 of 200 and 353 of 353 positions, NODES AND BESTMOVES, with every named sum EXACT.** R5: the planted fault IS reported (ASan, exit 1); the clean sanitizer build over O at T1: **0 sanitizer lines over 200 positions**.
**How sure:** certain — fourteen deterministic runs against fourteen committed jsons, zero differences anywhere.

## 2. Honesty numbers
My build /tmp/j4_tree/build/forge (sha 04bcba3d…, bit-identical to long 5c's and long 19's composition source); pins re-run for this item (hon/ in the folder): all four exact.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 sha + build | done | hon/ + R1.txt | sha matches; built |
| R2 pins + uci | done | hon/honesty_*.txt, uci.txt | four exact; ten options with kimi5's defaults |
| R3/R4: the fourteen runs vs kimi5's jsons | done | cmp.txt | 200/200 + 353/353 nodes and bestmoves, ALL; the six named sums EXACT |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, exit 1 |
| R5 clean sanitizer (O, T1) | done | san/O_T1_d12.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md | all three items held |

## 4. Findings
1. **kimi5's job-11 reproduces COMPLETELY** — the identity ladder (i1→i4), the ±1/1024 resolution controls (c1 differs everywhere exactly as its sum says; c2 equals i2 exactly), and both T-trees: 14 runs × up to 353 positions, nodes and bestmoves, zero differences, on a build from a different machine.
2. My long-5c (sum-level) and long-21 (the RoundF sweep) are both superseded in precision by this position-by-position pass; the sweeps' conclusions stand unchanged.
3. Suspicions, not proven: none.

## 6. What I read from my colleagues
kimi5's REPORT_kimi5_job11.md (its I1–I4/C1/C2 structure and its T1/T2 bootstrap ratios — the ratios 1.0705/1.2542 match my long-26 counter runs' tree ratios to the fourth decimal); file 9's rule (applied from job 9 on).

## 7. What I did NOT do
The bootstrap re-sampling (kimi5's Part-2 statistics — its ratios are already confirmed by my deterministic tree sums).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
None this time.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long31/stamps.txt
?? forge-combo29/REPORT_deepseek6_long31.md
?? forge-combo29/tests_deepseek6_long31/cmp.txt
?? forge-combo29/tests_deepseek6_long31/hon/
?? forge-combo29/tests_deepseek6_long31/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long31/runs/
?? forge-combo29/tests_deepseek6_long31/san/
?? forge-combo29/tests_deepseek6_long31/uci.txt
$ ls forge-combo29/tests_deepseek6_long31/
CLAIM.txt
cmp.txt
hon
plant_evidence.txt
PREDICTION.md
runs
san
stamps.txt
uci.txt
```
