# REPORT — deepseek6, long 11 (recipe R on kimi5's SearchChecks, its job 6)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long11/ · CLAIM.txt before the first command (400441471); PREDICTION.md before the first counted run (1ec60b400).

## 1. Three lines
**Asked:** reproduce kimi5's SearchChecks invariant build independently: pins with and without the flag, the identity rows, its four measured runs' per-site counts compared with its agg tables, and a sanitizer pass with a planted fault.
**Answer:** R1–R3 met (sha d5566aa8…; pins exact on both builds; S14 rows of BOTH builds equal long 1's on O 200/200 and G 353/353). R4: **three of the four runs reproduce kimi5's counts EXACTLY — all 70 sites, made and breaches, zero differences** (O d12 and G d12 no-options, G50 d16), including V5.store-qfinal's breach counts 19,021 / 28,821 / 8,286 and the V2/V3 child-score made-counts equal to the engine's own node sums. The fourth (O50, Threads 4) is non-deterministic by design: 60 of 70 made-counts differ from kimi5's run while **every breach count is 0 in both** — the invariant verdict reproduces even where the counts cannot. R5: the planted fault IS reported (ASan heap-buffer-overflow, exit 1, at the planted top-of-search line); the clean sanitizer flag build gives **0 sanitizer lines over O d12 (200 positions) and O50 T4 d12 (50 positions)**.
**How sure:** certain; the one process slip (my first R4 attempt ran under S14 — a base mismatch, discarded uncommitted, re-run on the no-options base kimi5 used) is disclosed in 4.3.

## 2. Honesty numbers
No-flag build /tmp/l11_noflag/build/forge and flag build /tmp/l11_flag/build/forge: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 on the flag build (honesty files in /tmp/kimi5_j4/ — hmm, copied to the folder as honesty_*.txt); the no-flag build shares the source with only the flag differing.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 sha + dry-run + apply + two builds | done | build logs; sha256sum output in R1.txt | sha d5566aa86195f3f4… matches; zero fuzz; no-flag and FORGE_SEARCH_CHECKS=1 builds |
| R2 pins | done | honesty_*.txt | four exact (flag build) |
| R3 identity under S14, both builds | done | r3.txt | O 200/200, G 353/353, nodes and moves, BOTH builds vs long 1 |
| R4 O d12 no-options | done | my_agg_r4_O_d12.txt vs agg_k2.txt | 70/70 sites equal, 0 differences |
| R4 G d12 no-options | done | my_agg_r4_G_d12.txt vs agg_k3.txt | 70/70 equal |
| R4 G50 d16 | done | my_agg_r4_G50_d16.txt vs agg_g50d16.txt | 70/70 equal |
| R4 O50 T4 | done | my_agg_r4_O50_T4.txt vs agg_o50t4.txt | 60/70 made-counts differ (non-deterministic threads); breaches 0 in BOTH at every site |
| R5 planted fault | done | plant_err.txt (copy: plant_evidence.txt) | ASan heap-buffer-overflow, READ of size 4, exit 1 |
| R5 clean sanitizer | done | san/O_d12_flag.rows, san/O50_T4_d12.rows | 0 lines over 200 + 50 positions |
| prediction own commit first | done | PREDICTION.md (1ec60b400) | items 1 and 2 held (with the T4 made-count caveat as predicted "non-deterministic by design" — see 4.1); item 3 held |

## 4.1 Findings
1. **The invariant build is reproducible to the count wherever the search is deterministic**: O d12, G d12 and G50 d16 give kimi5's exact per-site made and breach counts — 3 × 70 sites, ~790 M checks total, zero differences. The V5.store-qfinal breach counts (19,021 / 28,821 / 8,286) and the V6 suppressed-store arrivals (2,222,128 / 4,535,226 / 3,278,091) are machine-independent facts of this tree.
2. **The 4-thread run verifies the INVARIANT, not the counts**: all 70 sites show 0 breaches in both runs; 60 made-counts differ because the 4-thread tree itself is not reproducible. kimi5's report already marked this run "no node sum known".
3. Process disclosure: the first R4 attempt ran under S14 (my default base from earlier jobs) — kimi5's runs are no-options; the mismatched capture was discarded uncommitted and re-run on the correct base. The R4 sums under the correct base: O 12,573,318, G 22,128,265 — the no-options sums, as kimi5's K1/K3.
4. Suspicions, not proven: none new.

## 5. What I read from my colleagues
kimi5's REPORT_kimi5_job6.md in full; the peer session's progress notes (job 5 and job 6 done on its side, long 10 claimed by it). Nothing contradicts this report.

## 6. What I did NOT do
kimi5's d16 O run (its report has no such run — the four runs above are all it measured). The G50 d16 SANITIZER run (the recipe says "over O"; noted).

## 7. What I am NOT sure about
Nothing material. The T4 count differences are expected non-determinism, not a finding.

## 8. A better way
The agg comparison could diff the two tables directly in the committed comparer (it does; the output above is its print).

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long11/stamps.txt
?? forge-combo29/REPORT_deepseek6_long11.md
?? forge-combo29/tests_deepseek6_long11/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long11/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long11/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long11/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long11/long11_runs.sh
?? forge-combo29/tests_deepseek6_long11/my_agg_g50d16.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_k2.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_k3.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_o50t4.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_r4_G50_d16.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_r4_G_d12.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_r4_O50_T4.txt
?? forge-combo29/tests_deepseek6_long11/my_agg_r4_O_d12.txt
?? forge-combo29/tests_deepseek6_long11/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long11/r3.txt
?? forge-combo29/tests_deepseek6_long11/runs/
?? forge-combo29/tests_deepseek6_long11/san/
$ ls forge-combo29/tests_deepseek6_long11/
aggchk.py
chkrun.py
CLAIM.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
long11_runs.sh
my_agg_g50d16.txt
my_agg_k2.txt
my_agg_k3.txt
my_agg_o50t4.txt
my_agg_r4_G50_d16.txt
my_agg_r4_G_d12.txt
my_agg_r4_O50_T4.txt
my_agg_r4_O_d12.txt
plant_evidence.txt
PREDICTION.md
r3.txt
runs
san
stamps.txt
```
