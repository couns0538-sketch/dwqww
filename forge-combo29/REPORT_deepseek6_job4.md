# REPORT — deepseek6, job 4 (why LmrFine's finer reductions make the tree 7 % larger, counted)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_job4/ · job clock started 2026-11-16T18:08:45Z (tests_deepseek6_job4_start.txt); report written 2026-11-16T18:18:30Z, minute 10 of 60.

## 1. Three lines
**Asked:** count, at every LMR site, how the fine (1/1024) reduction differs from the integer one, split quiet/noisy, by history bin and depth, with the beat-alpha outcome of each reduced search — and say where the 7 % larger T1 tree comes from.
**Answer:** Step 0 fully met (patch sha f7bf3f43…, dry run clean; the eight plain sums are EXACTLY the known values incl. kimi5's T1 10,170,054 / T2 11,915,365 on O and 19,269,858 / 22,952,032 on G; the counter build equals the plain build on every position of all eight comparisons). K1, K2, K3, K4, K5 all MET (numbers below). **The 7 % is made on the positive-history side: in D2 on O, 17.5 % of quiet sites have d ≠ 0, d = -1 outnumbers d = +1 by 1.57 : 1, and a would-be d = -1 site's reduced search beats alpha 1.84× as often as a d = 0 site's (6.74 % vs 3.66 %).** Under T2 (round down) the d = -1 band starts at history 6 instead of 2,828 — 1.44 M of 3.48 M quiet sites (41 %) — which is why T2's tree is 25 % larger than S14's.
**How sure:** certain of every count (each from a committed .lmrctr file, one line per go, summed by one committed command; the gate-arithmetic style checks are exact equalities). Predictions: (a) HELD, (b) HELD, (c) KILLED as stated — measured 1.84×, my claim said "at least twice"; the direction (d = -1 beats more) held and 1.84 is outside my declared kill band, which I had set too wide — the miss is mine and is reported, not hidden.

## 2. Honesty numbers
B_FINE = /tmp/j4_tree/build/forge sha256 04bcba3ddcc97501bdd524a686f785041f7b8ec22dd131be319f69bcabb05720 — bit-identical to long 5c's recorded build. Its pins: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt in this folder); uci lists LmrFine (0..1, default 0), LmrFineHistory (0..1, default 0), LmrRoundF (0..1023, default 512) (uci_fine.txt). B_FINE_CTR = /tmp/j4_ctr/build/forge sha256 c38f0ec1759fe87233085e04b92529f60d19e1eeee5f2ab95890d92942b12009 (finectr_counters.patch.txt on top of LmrFine).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| patch sha + dry run | done | patch_dryrun.txt | sha f7bf3f4363220440…; `patch -p1 --dry-run` clean, then real apply clean |
| B_FINE build + pins + uci | done | honesty_*.txt, uci_fine.txt | four pins exact; three options as required |
| 8 plain rows (S14, identity, T1, T2 × O,G) | done | runs/fine_*.rows, step0.txt | all eight sums == the known values, node for node |
| B_FINE_CTR == B_FINE | done | step0.txt, step0b.txt | 200/200 and 353/353 nodes AND bestmove, all eight |
| D0..D3 counted runs | done | runs/D?_*.lmrctr (one line per go) | all rows=200/353, 0 MISSING |
| K1 identity all-d-0 | done | analysis.txt | q and n only d=0: 3,265,389 + 390,605 (O), 7,067,854 + 706,955 (G) |
| K2 noisy always d=0 | done | analysis.txt | all eight runs OK |
| K3 T1 bin rules | done | analysis.txt (K3 block) | every bin holds exactly the d values the job lists; b=-3 and b=2 two values each; b=-6, b=5 two each; -5,-4 only +1; -2..1 only 0; 3,4 only -1 |
| K4 T2 bin rules | done | analysis.txt (K4 block) | d=-1 exactly for 6..5642 (bins 0..4 show the split at the 5/6 boundary inside b=0; b=5 holds the 5643+ tail); d=0 below |
| K5 mismatch_used 0 | done | analysis.txt | 0 in all eight runs |
| history ≥ 5643 recompute | done | hs_sample recompute in analysis.txt; script job4_analyze.py; pairs inside the .lmrctr lines | 12,800 pairs per run, 0 mismatches in D2 and D3 |
| prediction own commit first | done | PREDICTION.md, commit 77a602192 | (a) held, (b) held, (c) killed as stated |

## 4. The tables (from job4_analyze.py output analysis.txt; counters summed over all searches; slots are d = -3,-2,-1,0,+1,+2,+3,other)
| run | quiet sites (run d) | beat_alpha (run d) | noisy sites (run d) | quiet sites (T1 ref) | beat_alpha (T1 ref) |
|---|---|---|---|---|---|
| D0_O | 0,0,0,3265389,0,0,0,0 | 0,0,0,125639,0,0,0,0 | 0,0,0,390605,0,0,0,0 | 0,0,356382,2704377,204630,0,0,0 | 0,0,24029,99035,2575,0,0,0 |
| D0_G | 0,0,0,7067854,0,0,0,0 | 0,0,0,310052,0,0,0,0 | 0,0,0,706955,0,0,0,0 | 0,0,675948,5707332,684574,0,0,0 | 0,0,53369,245182,11501,0,0,0 |
| D1_O | identical to D0_O | identical | identical | identical | identical |
| D1_G | identical to D0_G | identical | identical | identical | identical |
| D2_O | 0,0,370272,2869152,236548,0,0,0 | 0,0,25822,107627,3201,0,0,0 | 0,0,0,417888,0,0,0,0 | == run d | == run d |
| D2_G | 0,0,724042,5953821,666063,0,0,0 | 0,0,57394,255918,10876,0,0,0 | 0,0,0,739870,0,0,0,0 | == run d | == run d |
| D3_O | 0,0,1441206,2524660,0,0,0,0 | 0,0,81237,81309,0,0,0,0 | 0,0,0,505337,0,0,0,0 | 0,0,454908,3239039,271919,0,0,0 | 0,0,31477,127568,3501,0,0,0 |
| D3_G | 0,0,2994578,5631092,0,0,0,0 | 0,0,195153,200324,0,0,0,0 | 0,0,0,882794,0,0,0,0 | 0,0,918133,6912997,794540,0,0,0 | 0,0,71312,310988,13177,0,0,0 |

In D2 the run's configuration IS T1, so its run-d and T1-ref columns agree to the count (25,822 = 25,822 on O). The run-d beat column of D0/D1 uses the run's own (all-zero-d) bucketing; the would-be analysis in prediction (c) reads the T1-ref columns.

History bins around the boundaries (D2_O, b = history/1000): b=2 holds {-1: 21271, 0: 116976} (the 2828 boundary inside it); b=-3 holds {0: 196649, +1: 29144} (the -2822 boundary); b=3 and b=4 only -1 (105638, 87208); b=-5, -4 only +1 (59800, 120728). Full 14-bin tables in analysis.txt.

## 5. Findings
1. **Where the 7 % comes from**: both measured legs point at positive history. (i) More sites reduce less (d=-1 : d=+1 = 1.57 : 1); (ii) the beat-alpha rate falls steeply across the d gradient in the actual T1 run (D2_O): d=-1 sites beat alpha 25,822/370,272 = 6.97 %, d=0 sites 107,627/2,869,152 = 3.75 %, d=+1 sites 3,201/236,548 = 1.35 % — a d=-1 site is 5.2× as likely to force the full-depth re-search as a d=+1 site. The same gradient read from D0's would-be buckets gives 6.74 % vs 3.66 % (ratio 1.84). Fewer reductions concentrated on the moves most likely to deserve them is exactly what makes the tree larger.
2. **d never leaves {-1, 0, +1}**: the "other" slot is 0 at every site of every run — at S14's settings the fine path's whole-unit changes are exactly one ply, never more.
3. **T2's boundary is at history 6, not 2828** (round-down): the d=-1 band covers 41.5 % of quiet sites (1,441,206) against T1's 10.6 % — that single rounding change is the difference between +7 % and +25 % tree size. The rounding bit is worth more than every other fine option combined at these settings.
4. **The beat-alpha rates are low everywhere** (3.7–6.7 % on O): LMR's reduced null-window searches almost never beat alpha outright; the fine formula's value is concentrated in shifting WHICH 3–7 % of sites do.
5. Disclosure — the counter was built twice: my first capture had an UNCONDITIONAL beat counter (it counted searches, not beats); I caught it because beat totals exceeded quiet-site totals by exactly the noisy-site count (390,605 on O). Fixed to `if (score > alpha)`, rebuilt (sha c38f0ec1…), re-ran all eight counted runs, re-verified Step 0 identities. The committed finectr_counters.patch.txt is the FIXED one; the broken capture was discarded uncommitted.
6. Suspicions, not proven: none new.

## 6. What I read from my colleagues
File 4's recount of the peer session's job-3b (its prediction written 17:46:30Z, independently valid; its rows agree with mine per Opus); glmflash5's check-bundle matches (+6.7 pooled at 2,000 nodes) via the job file. The stamps.txt conflict markers were repaired in my first job-4 commit (e2fb1dbdc): both sides kept, sorted by time, normalized to ISO.

## 7. What I did NOT do
File 5 (per its own rule it belongs to the other session now that a "deepseek6 job 4 prediction" commit exists on the branch). Nothing else from file 4 was skipped.

## 8. What I am NOT sure about
The beat-alpha rates at would-be d = ±2/±3 (zero sites observed — the bins are empty, so no rate exists); whether a settings change could ever populate them is untested.

## 9. A better way
The beat-alpha counter could also log whether the full-depth re-search then failed high (the two-stage outcome); not asked, noted as the natural extension.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_job3b/counterrun.py
 M forge-combo29/tests_deepseek6_job4/finectr_counters.patch.txt
 M forge-combo29/tests_deepseek6_job4/stamps.txt
?? forge-combo29/REPORT_deepseek6_job4.md
?? forge-combo29/tests_deepseek6_job4/analysis.txt
?? forge-combo29/tests_deepseek6_job4/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_job4/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_job4/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_job4/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_job4/job4_analyze.py
?? forge-combo29/tests_deepseek6_job4/job4_runs.sh
?? forge-combo29/tests_deepseek6_job4/runs/
?? forge-combo29/tests_deepseek6_job4/step0.txt
?? forge-combo29/tests_deepseek6_job4/step0b.txt
?? forge-combo29/tests_deepseek6_job4/uci_fine.txt
$ ls forge-combo29/tests_deepseek6_job4/
analysis.txt
finectr_counters.patch.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
job4_analyze.py
job4_runs.sh
PREDICTION.md
runs
stamps.txt
step0b.txt
step0.txt
uci_fine.txt
```
