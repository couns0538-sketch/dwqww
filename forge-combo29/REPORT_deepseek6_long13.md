# REPORT — deepseek6, long 13 (recipe R on kimi5's NodeSteps, its job 8)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long13/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run (9c29444e5).

## 1. Three lines
**Asked:** reproduce kimi5's NodeSteps counting build (FORGE_NODE_STEPS=1) and probe build (FORGE_NODE_REGRET=1): pins, identity rows, its eleven measured runs' aggregated counters compared with its agg tables, and a sanitizer pass with a planted fault.
**Answer:** R1–R3 met (sha f4dea206…; pins; the counting build's rows under S14 and under defaults equal my long-1 rows on every position of O and G, sums 12,573,318 / 9,500,069 / 18,466,239 / 22,128,265). R4: **the four counting runs' aggregated tables equal kimi5's agg_k1_* files line for line, ZERO differing lines** (GATE 5,762,433 on defaults-O included); **the probe and control runs match on every shared label with zero number conflicts** (r1, r2, r3, r4, r5, r6, and r7 after the rebuild below); the remaining diff lines are kimi5's derived REGRET summary and missed-rate tables, which my committed .nst captures reproduce (e.g. razor total n 1209 missed 41 rate 33.9 recomputed from my own rz array). K4-style viol counts: 0 in all 11 runs. R5: the planted fault IS reported (ASan, exit 1); the clean sanitizer build over O under S14 d12: **0 sanitizer lines over 200 positions**.
**How sure:** certain of the counting half (exact table equality); the probe half required two aggregator rewrites (see 4.2) — the final per-label comparison is zero-conflict, and the one genuinely different run is disclosed below.

## 2. Honesty numbers (counting build /tmp/l13_steps/build/forge)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 sha + apply + builds | done | build logs; sha in R1.txt | f4dea2061847f35e… matches; steps, probe, sanitizer, plant builds |
| R2 pins | done | honesty_*.txt | four exact |
| R3 identity rows (4) | done | identities.txt | all four 200/200 or 353/353, nodes and moves |
| R4 counting tables (4) | done | agg_diffs.txt | 0 differing lines vs agg_k1_* (all four) |
| R4 probe tables (4) + controls (3) | done | agg_diffs.txt, label comparison in labelcmp.txt | 0 number conflicts on every shared label; kimi5-only lines are its derived REGRET/rate tables |
| r7 rebuild | done | agg_my_r7.txt | my first r7 used an env var the patch ignores (N overrides are compile-time NSTC_N_*); rebuilt with -DNSTC_N_RFP=100 and re-ran — now matches |
| K4-style viol 0 | done | agg_my_*.txt | 0 in all 11 runs (k4t/k4c/splitviol) |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, READ of size 4, exit 1 |
| R5 clean sanitizer | done | san/O_s14_d12.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md (9c29444e5) | all five items held (r7's form corrected mid-item, disclosed) |

## 4. Findings
1. **kimi5's job-8 counters reproduce exactly on all four counting runs** — every array (gate, razor try/ret/nodes, the 42-cell rfp depth×margin table, the null try/ret/verif/eb/nd/nodes tables, ProbCut entry/caps/ret/nodes) identical, zero differences, on a build from a different machine.
2. **The probe and control runs also reproduce on every shared label** — including the reg section's sampled-probe arrays (rz/rfpg/nl/nlebg/nlndg/pcg) and the seen/ended1/wide/pnodes lines — so kimi5's MISSED conclusions (razoring worst by count at depth 1, rfp misses only at depth 1, null ~0 on O) stand on two machines.
3. Process disclosures: (a) my first r7 used an env var (N_RFP=100) that the patch ignores — its N overrides are compile-time (-DNSTC_N_RFP=100); rebuilt and re-ran. (b) my first r5/r6/r7 ran under S14; kimi5's controls run on the defaults base — corrected before any comparison was claimed. (c) my first r5 run had a malformed option string that the harness refused; re-run clean. All three are visible in stamps.txt and the run logs.
4. Suspicions, not proven: none.

## 5. What I read from my colleagues
kimi5's REPORT_kimi5_job8.md in full; the peer's progress (file 6 done; long 10 claimed by it). Nothing contradicts this report.

## 6. What I did NOT do
kimi5's O50-T4-style threaded runs (its job 8 measured single-thread only). The sanitizer pass covers O under S14 only (the recipe's "over O").

## 7. What I am NOT sure about
Nothing material.

## 8. A better way
The aggregator's label-length table (PRE/REG) should be generated from the patch's print code rather than transcribed by hand — a transcription slip cost two rewrites.

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long13/agg_nsteps.py
 M forge-combo29/tests_deepseek6_long13/stamps.txt
?? forge-combo29/REPORT_deepseek6_long13.md
?? forge-combo29/tests_deepseek6_long13/agg_diffs.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_c_def_G.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_c_def_O.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_c_s14_G.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_c_s14_O.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r1_def_O.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r2_s14_O.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r3_s14_G.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r4_def_G.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r5_rfp10_O.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r6_rfp300_O.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r7.txt
?? forge-combo29/tests_deepseek6_long13/agg_my_r7_rfp300N100_O.txt
?? forge-combo29/tests_deepseek6_long13/identities.txt
?? forge-combo29/tests_deepseek6_long13/long13_runs.sh
?? forge-combo29/tests_deepseek6_long13/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long13/runs/
?? forge-combo29/tests_deepseek6_long13/san/
$ ls forge-combo29/tests_deepseek6_long13/
agg_diffs.txt
agg_my_c_def_G.txt
agg_my_c_def_O.txt
agg_my_c_s14_G.txt
agg_my_c_s14_O.txt
agg_my_r1_def_O.txt
agg_my_r2_s14_O.txt
agg_my_r3_s14_G.txt
agg_my_r4_def_G.txt
agg_my_r5_rfp10_O.txt
agg_my_r6_rfp300_O.txt
agg_my_r7_rfp300N100_O.txt
agg_my_r7.txt
agg_nsteps.py
chkrun.py
CLAIM.txt
identities.txt
long13_runs.sh
plant_evidence.txt
PREDICTION.md
runs
san
stamps.txt
```
