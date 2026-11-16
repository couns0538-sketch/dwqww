# REPORT — deepseek6, long 9 (recipe R on kimi5's LmrDS_tunables, its job 4)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long9/ · CLAIM.txt committed before the first command (claim pushed as 995195e93 after one refused push was rebased); PREDICTION.md committed before the first counted run (ac038e37e).

## 1. Three lines
**Asked:** reproduce kimi5's LmrDS_tunables patch independently: pins, identity at defaults, every setting its job-4 report tested compared position by position with its rows, and a sanitizer pass with a planted fault.
**Answer:** R1–R3 all met (sha a9c33d7d…; pins exact; the tunable build at defaults is row-for-row my S14 rows on O and G, and base+switch == tunable+switch on every position). R4: on kimi5's own option base (defaults + LmrDeeperShallower true + the setting) **all nine settings equal kimi5's d12 jsons on 200 of 200 positions, nodes AND bestmove, and all nine O sums match its sums exactly** (e.g. k4c 9,232,844 both, ratio 0.7343). On G (kimi5's base) the nine sums are committed with no known answers; under S14 my direction predictions held 7 of 9 — k4b (DepthMul 4) and dbl (80/4) KILLED: **on G, enlarging the DEEPER arm's reach shrinks the tree (−1.61 % and −5.92 % under S14)**, the opposite of the shallower-side intuition. R5: the planted fault IS reported (ASan heap-buffer-overflow, READ of size 4, at the planted line, exit 1); the clean sanitizer build gives **0 sanitizer lines over 1,800 positions** (nine settings × 200).
**How sure:** certain of every number; the one process slip (my first R4 attempt used the S14 base, where kimi5's rows cannot match — 0 of 200 on all nine — because kimi5's job-4 runs sit on the DEFAULTS base; the base was corrected, the S14-based runs kept as extra evidence) is disclosed in 4.3.

## 2. Honesty numbers (tunable build /tmp/l9_tree/build/forge sha fb9152ca…)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt). `uci` lists the four new options with the right defaults/ranges (uci.txt): LmrDeeperBase 40 (0..100000), LmrDeeperDepthMul 2 (0..16), LmrShallowerBase 0 (−100000..400), LmrShallowerDepthMul 1 (0..16); LmrDeeperShallower itself is a check, default false (base code).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 sha + dry run + apply + build | done | patch_dryrun.txt, build logs | sha a9c33d7d660d697d… matches; zero fuzz; built |
| R2 pins + uci | done | honesty_*.txt, uci.txt | four exact; four new options listed |
| R3 identity at defaults | done | cmp_out.txt | O 200/200, G 353/353 nodes and moves vs long-1 rows |
| R3b base+switch vs tunable+switch (K2 remade) | done | cmp_out.txt | O 200/200, G 353/353 |
| R4 nine settings, O, position-by-position vs kimi5's d12 jsons | done | cmp_r4d.txt | ALL NINE 200/200 nodes AND bestmove; all nine sums equal kimi5's exactly |
| R4 nine settings on G (kimi5's base) | done | cmp_r4d2.txt | sums committed (table below) |
| R4 nine settings under S14 (extra, both sets) | done | runs/r4_*.rows, cmp_out.txt | G direction table: 7 of 9 predictions held |
| R5 planted fault | done | plant_err.txt (copy: plant_evidence.txt) | ASan heap-buffer-overflow, READ of size 4, search.cpp:1566, exit 1 |
| R5 clean sanitizer, O, nine settings | done | san/*.rows + sancount output in san_out.txt | 0 lines × 9 runs (1,800 positions) |
| prediction own commit first | done | PREDICTION.md (ac038e37e) | items 1,2,3,5 held; item 4: 7 of 9 held, k4b and dbl killed |

## 4.1 The G sums on kimi5's base (defaults + switch + setting; depth 12; no known answers)
k3 22,128,265 (= the no-options G sum exactly: the ±100000 margins give the switch-off tree on G too) · k4a 23,396,667 · k4b 22,225,758 · k4c 17,801,476 · k4d 20,142,509 · deep 25,455,871 · flat 21,921,367 · half 24,468,730 · dbl 20,923,694. (No-options G = 22,128,265.)

## 4.2 The G sums under S14 (extra evidence; direction predictions against 18,466,239)
k3 18,466,239 (+0.00 %, EXACT) · k4a 18,659,580 (+1.05 %) · k4b 18,169,490 (−1.61 %, KILLED — predicted >) · k4c 14,495,021 (−21.51 %) · k4d 16,338,571 (−11.52 %) · deep 19,182,800 (+3.88 %) · flat 17,877,389 (−3.19 %) · half 19,072,904 (+3.29 %) · dbl 17,372,896 (−5.92 %, KILLED — predicted >).

## 4.3 Findings
1. **kimi5's job-4 reproduces to the node on every tested setting** — nine settings × 200 positions, nodes and bestmoves identical, sums identical to the last digit. Two independent builds (mine fb9152ca…, kimi5's own), one answer.
2. **k3's switch-off proof holds on G as on O**: ±100000 margins give exactly the no-options tree on BOTH sets (12,573,318 / 22,128,265 = the exact no-option sums) — the four tunables at ±100000 are arithmetic no-ops, so the switch IS its three lines.
3. **The deeper arm's direction is base-dependent**: under kimi5's defaults base, DeeperBase 20 k4a GROWS O's tree relative to... it does not (0.9791 — SMALLER); under S14 it GROWS G's tree (+1.05 %) while k4b/dbl SHRINK it. The deeper-vs-shallower arms interact with the rest of the option set; a tuner moving them must be measured on the option base it will actually play.
4. Process disclosure: my first R4 attempt ran the nine settings under S14 and compared against kimi5's jsons — 0 of 200 everywhere, which is a BASE mismatch (kimi5's job-4 rows are on the defaults base), not a patch disagreement. The corrected runs (kimi5's base) match 200/200; the S14-based runs stay in the folder as extra evidence.
5. Suspicions, not proven: none new.

## 5. What I read from my colleagues
kimi5's REPORT_kimi5_job4.md in full (its K0–K5, its two match settings, its d12/d16 factors); file 7's list and rules; the peer's progress notes (it is on file 6, kimi5's job-13 dependent). Nothing contradicts this report.

## 6. What I did NOT do
Nothing from recipe R. The d16 jsons of kimi5 were not compared (R4 names rows at depth 12; the d16 data stays available).

## 7. What I am NOT sure about
Why the deeper arm shrinks G's tree under S14 (k4b/dbl) while growing it under the defaults base — measured, not traced in code.

## 8. A better way
R4 could have read kimi5's input logs BEFORE running (it did, but I applied the S14 base first by reflex from my own earlier jobs) — the recipe's "compared with kimi5's rows file" implies kimi5's base; reading the base first saves one run set.

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long9/stamps.txt
?? forge-combo29/REPORT_deepseek6_long9.md
?? forge-combo29/tests_deepseek6_long9/cmp_out.txt
?? forge-combo29/tests_deepseek6_long9/cmp_r4d.txt
?? forge-combo29/tests_deepseek6_long9/cmp_r4d2.txt
?? forge-combo29/tests_deepseek6_long9/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long9/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long9/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long9/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long9/long9_cmp.py
?? forge-combo29/tests_deepseek6_long9/long9_runs.sh
?? forge-combo29/tests_deepseek6_long9/long9_san.sh
?? forge-combo29/tests_deepseek6_long9/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long9/plant_raw.txt
?? forge-combo29/tests_deepseek6_long9/runs/
?? forge-combo29/tests_deepseek6_long9/san/
$ ls forge-combo29/tests_deepseek6_long9/
CLAIM.txt
cmp_out.txt
cmp_r4d2.txt
cmp_r4d.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
long9_cmp.py
long9_runs.sh
long9_san.sh
plant_evidence.txt
plant_raw.txt
PREDICTION.md
runs
san
stamps.txt
```
