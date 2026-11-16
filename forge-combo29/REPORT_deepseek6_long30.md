# REPORT — deepseek6, long 30 (recipe R on LmrCutNode 5859a66f, LmrGiveCheck 0e5b0375, LmrTtPv 05e49972 — one at a time)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long30/ · CLAIM.txt before the first command; stamps per stage; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** recipe R on kimi5's three job-7 spin-off patches, one at a time, with R4 = the setting each tested in its job-7 report (CutNode=1, TtPv=0, GiveCheck=0) compared position by position with its rows files.
**Answer:** **all three patches pass R1–R3** (shas match file 8's; pins exact x3; the six identity runs under S14 equal my long-1 rows 200/200 and 353/353 — nodes AND moves). **R4: all six alt-value runs on kimi5's defaults base equal its o1_v1/o2_v0/o3_v0 jsons EXACTLY — sums 12,310,830 / 22,228,946 (CutNode=1), 8,572,032 / 16,869,889 (TtPv=0), 11,811,886 / 21,239,639 (GiveCheck=0), with 200/200 and 353/353 node-equality per run.** R5: the planted fault IS reported (ASan, exit 1); the three clean sanitizer builds give **0 sanitizer lines over 600 positions** (O at each alt value).
**How sure:** certain; the one process slip (my first six alt-value runs used the S14 base — kimi5's are defaults-based; discarded uncommitted, re-run correctly — the THIRD time this base reflex has fired, now a named rule in my notes) is disclosed in 4.2.

## 2. Honesty numbers (the three builds: /tmp/l30_LmrCutNode, /tmp/l30_LmrTtPv, /tmp/l30_LmrGiveCheck)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — run on each (honesty files per build in the folder, 4 files x 3).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 shas + dry runs + three builds | done | R1.txt, build logs | all three shas match file 8 (5859a66f / 0e5b0375 / 05e49972); zero fuzz |
| R2 pins + uci | done | uci.txt | each lists its option: LmrCutNode spin 0..4 default 2; LmrTtPv spin 0..4 default 1; LmrGiveCheck spin 0..4 default 1 |
| R3 identity x6 | done | cmp.txt identity lines | all 200/200 and 353/353, nodes and moves |
| R4 six alt-value runs vs kimi5's jsons | done | cmp2.txt | all six EXACT sums + node-for-node |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, exit 1 |
| R5 clean sanitizer x3 | done | san/*.rows | 0 lines x 600 positions |
| prediction own commit first | done | PREDICTION.md | all items held (after the base correction) |

## 4. Findings
1. **kimi5's three job-7 spin-off patches reproduce to the node on their tested settings** — six runs, 1,106 positions, zero differences, on a different machine and without its calib flag (the counters are observe-only, so its flag-build rows and my plain rows are the same tree — confirmed by the exact matches).
2. **The base rule, learned the hard way and now stated**: kimi5's rows are on the DEFAULTS option base unless its report says otherwise; every recipe-R comparison must read its input log first. This is the third instance (longs 9, 11, 30).
3. My long-2/3 reports' earlier sum-level verification of these three patches is now superseded by this position-by-position one (same patches, shas now verified).
4. Suspicions, not proven: none.

## 6. What I read from my colleagues
kimi5's REPORT_kimi5_job7.md section 4.5 (the three patches' other-value sums and its proof-build form); file 8's sha list. Nothing contradicts this report.

## 7. What I did NOT do
The wrong-name refusal test of kimi5's form (its o1_wrongname.txt proves the harness path; my harness's refusal stop is already proven in long 1's stopcheck files).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The three builds could have shared one tree with the option patches applied one at a time and three binaries — three clean builds were simpler and equally fast.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long30/stamps.txt
?? forge-combo29/REPORT_deepseek6_long30.md
?? forge-combo29/tests_deepseek6_long30/cmp.txt
?? forge-combo29/tests_deepseek6_long30/cmp2.txt
?? forge-combo29/tests_deepseek6_long30/runs/
?? forge-combo29/tests_deepseek6_long30/san/
$ ls forge-combo29/tests_deepseek6_long30/
CLAIM.txt
cmp2.txt
cmp.txt
PREDICTION.md
runs
san
stamps.txt
```
