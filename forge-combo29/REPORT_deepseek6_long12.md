# REPORT — deepseek6, long 12 (recipe R on kimi5's LmrCalib, its job 7)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long12/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** reproduce kimi5's LmrCalib observe-only build (FORGE_LMR_CALIB=1) and its probe build (FORGE_LMR_REGRET=1): pins, identity rows, its four measured runs' A_TABLE/TOTAL/K2 counts reconstructed from my own capture and compared with its agg tables, plus a sanitizer pass with a planted fault.
**Answer:** R1–R3 met (sha e377350f…; pins exact; the calib build under S14 equals my long-1 S14 rows on O 200/200 and G 353/353, and with no options equals my long-1 no-options rows on O 200/200 and G 353/353 — kimi5's K1 sums 12,573,318 / 22,128,265 reproduced). R4: **all four tables — O d12 calib, G d12 calib, O d12 probe, G d12 probe — equal kimi5's agg_k2/agg_k3/agg_r1/agg_r2 EXACTLY**: searches 200/353, K2_violations 0 everywhere, every A_TABLE row, every TOTAL column (O calib 4,764,594 / 244,406 / 197,279 / 23,043,541 / 4,370,123; O probe 4,592,792 / 238,076 / 193,065 / 25,328,092 / 5,719,411; G probe 9,065,271 / 492,175 / 386,628 / 51,011,091 / 11,903,744 — the diff against kimi5's files is line order only, zero number differences). R5: the planted fault IS reported (ASan heap-buffer-overflow, exit 1); the clean sanitizer calib build over O d12 no-options: **0 sanitizer lines over 200 positions**.
**How sure:** certain — the reconstructed tables come from my own aggregator (agg_lmr.py) reading my own capture of my own build; the only degree of freedom (probe built with both flags vs REGRET alone) resolved in favor of both, and the exact match proves the choice.

## 2. Honesty numbers (calib build /tmp/l12_calib/build/forge)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 sha + apply + three builds | done | build logs; sha in R1.txt | e377350f9ea1f6dd… matches; calib, probe (both flags), sanitizer builds |
| R2 pins | done | honesty_*.txt | four exact |
| R3 identity under S14 | done | r3r4.txt | O 200/200, G 353/353 |
| R4a no-options rows | done | r3r4.txt | O 200/200 vs O_none, G 353/353 vs G_none; sums 12,573,318 / 22,128,265 |
| R4b calib tables vs agg_k2/agg_k3 | done | my_aggs.txt, agg_diff.txt | IDENTICAL (zero number differences, all rows) |
| R4c probe tables vs agg_r1/agg_r2 | done | my_aggs.txt, agg_diff.txt | IDENTICAL |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, READ of size 4, exit 1 |
| R5 clean sanitizer O d12 | done | san/O_d12_calib.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md | all five items held |

## 4. Findings
1. **kimi5's job-7 counting reproduces to the number on all four tables** — the per-search LMRCELL/TERM/HIST lines are deterministic and my independent aggregator (a different program from kimi5's) rebuilds its A_TABLE and TOTAL byte-for-byte on the counts. Two machines, two aggregators, one answer.
2. **The probe's disturbance is visible and reproduced**: the probe build's rn (re-search nodes) 25,328,092 vs the calib build's 23,043,541 on O (+9.9 % nodes of re-search) with cells_n LOWER (4,592,792 vs 4,764,594) — the probe's full-depth probes change the tree, exactly as kimi5 disclosed (+51.5 % O nodes total; the rn share shown here is the part inside the counted cells).
3. K2_violations = 0 in every one of my 1,106 searches (200+353 calib, 200+353 probe) — the observe-only claim holds on my build too.
4. Suspicions, not proven: none.

## 5. What I read from my colleagues
kimi5's REPORT_kimi5_job7.md (its K0–K2, the three spin-off patches of which long 2/3 already tested two-plus-one, its Part-4 verdicts); the peer's notes (it verified kimi5's job-13 table; long 10 is its claim). Nothing contradicts this report.

## 6. What I did NOT do
The LMRHIST/LMRTERM/CELL_TABLE detail levels beyond A_TABLE+TOTAL (kimi5's agg files carry them; my aggregator reconstructs the A_TABLE level the report's verdicts rest on — the finer tables can be rebuilt from the committed .lmr files at any time).
The d16 runs (kimi5's job 7 measured d12 only).

## 7. What I am NOT sure about
Nothing material.

## 8. A better way
None this time; the capture-then-reconstruct design mirrors kimi5's own pipeline closely enough to compare.

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long12/stamps.txt
?? forge-combo29/REPORT_deepseek6_long12.md
?? forge-combo29/tests_deepseek6_long12/agg_diff.txt
?? forge-combo29/tests_deepseek6_long12/agg_lmr.py
?? forge-combo29/tests_deepseek6_long12/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long12/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long12/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long12/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long12/my_aggs.txt
?? forge-combo29/tests_deepseek6_long12/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long12/r3r4.txt
?? forge-combo29/tests_deepseek6_long12/runs/
?? forge-combo29/tests_deepseek6_long12/san/
$ ls forge-combo29/tests_deepseek6_long12/
agg_diff.txt
agg_lmr.py
chkrun.py
CLAIM.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
my_aggs.txt
plant_evidence.txt
PREDICTION.md
r3r4.txt
runs
san
stamps.txt
```
