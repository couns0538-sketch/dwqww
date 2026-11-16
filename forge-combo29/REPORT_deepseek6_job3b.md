# REPORT — deepseek6, job 3b (where capture futility prunes, counted by depth and by deficit)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_job3b/ · job clock started 2026-11-16T17:42:12Z (tests_deepseek6_job3b_start.txt); report written 2026-11-16T17:54:00Z, minute 12 of 60.

## 1. Three lines
**Asked:** with the gate open (CaptureFutilityBase 230), at which lmr_depth does capture futility prune, how far below alpha must a capture stand, and does the gate's arithmetic match its behavior?
**Answer:** (1) Step 0 met for BOTH builds: the counter build's rows are bit-identical to the plain build's on O for S14 (200 of 200, 9,500,069) and for B0 (200 of 200, 9,562,828) — and beyond the requirement, C2/C3 on O and G also equal job 2's plain B3/B4 rows 200/200 and 353/353. (2) Known answer 1 MET (C1_O pruned[6] = 0; C3_O pruned[7] = 1, all of it in the single row 56 = job 2's position 57, one node; C1_G pruned[6] = 343 > 0). Known answer 2 MET in ALL 14 runs: gate_yes equals the prune total EXACTLY (e.g. C1_O 11,236 = 11,236; C1_G 51,491 = 51,491; C6_G 88,838 = 88,838) and bad_prune = 0 everywhere. (3) C1 on O: **largest pruning L = 3** (L0 0, L1 8051, L2 1941, L3 1074, L4 158, L5 12, L6 0; share at L ≤ 2 = 88.9 %). C1 on G: **largest pruning L = 6** (L1 25280, L2 11727, L3 9364, L4 3872, L5 905, L6 343; share at L ≤ 2 = 71.9 %).
**How sure:** certain of the counters (they reproduce every known answer, including the one-node B4 difference and its exact position); my prediction was 3-of-5 held, 2 killed — listed in 4.3.

## 2. Honesty numbers
Plain build (/tmp/glmflash5_base/build/forge, sha e06310ec…): job 2's files of this hour (honesty_bench11/13/16.txt, honesty_perft5.txt in tests_deepseek6_job2/ — 312866 / 862329 / 3024920 / 4865609, all exact; O_S14.rows 9,500,069, G_S14.rows 18,466,239). Counter build (/tmp/j3b_edit/build/forge, sha 20dc34b4…): its own four pins also exact (bench 11 312866, 13 862329, 16 3024920, perft 5 4865609 — files honesty_*.txt copied into this folder from /tmp/j3b_hon).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| counters.patch.txt (text patch, diff -u, no fuzz) | done | counters.patch.txt | 3 hunks: counter namespace at file scope in search.cpp, candidate/deficit/prune counting at the gate, reset+print in uci.cpp's go handler |
| counter build + pins | done | honesty_*.txt (this folder) | four exact |
| Step 0 identities | done | step0.txt | counter rows == plain rows, S14 and B0 on O, 200/200 nodes and moves |
| 14 counted runs | done | runs/C*_*.rows + runs/C*_*.cfp + job3b_runs.sh | all rc=0, one cfp line per go, 0 MISSING |
| plant (C0) | done | cfp_C0_C1_C3.txt | prn all 0 on both sets, bp 0 |
| known answer 1 | done | checks.txt | all three parts exact (row 56 one-node detail included) |
| known answer 2 | done | checks.txt, cfp_rest.txt | gy == prune total and bp == 0 in all 14 runs |
| prediction own commit first | done | PREDICTION.md (commit 3db68a9c8) | 3 held, 2 killed (4.3) |
| deficit tables per L | done | cfp_C0_C1_C3.txt, cfp_rest.txt (headers inside) | per-L bin counts, bins of 100, e < 0 → bin 0 |

## 4.1 The prunes by L (C1 = S14 + CaptureFutilityBase 230; counts summed over all searches by sumcfp.py)
| L | O pruned | O candidates | G pruned | G candidates | threshold T = 230 + 250·L |
|---|---|---|---|---|---|
| 1 | 8051 | 438002 | 25280 | 617424 | 480 |
| 2 | 1941 | 219824 | 11727 | 343703 | 730 |
| 3 | 1074 | 147134 | 9364 | 253530 | 980 |
| 4 | 158 | 39626 | 3872 | 81489 | 1230 |
| 5 | 12 | 26847 | 905 | 57463 | 1480 |
| 6 | 0 | 10071 | 343 | 29986 | 1730 |
| 7 | 0 | 5914 | 0 (CFD cap) | 18379 | 1980 |

## 4.2 The deficit picture (bins of 100; full per-L tables in cfp_C0_C1_C3.txt and cfp_rest.txt, each table headed)
The overwhelming mass of candidates sits in bin 0 (e < 0: the capture does not even reach alpha before the gate's extra terms): on O under C1, 78–80 % of candidates at every L ≤ 5; on G, 76–78 %. The gate's needed deficit grows by Multiplier (250) per ply, and the measured prunes thin out exactly as that slope predicts: on O the last prunes die between L3 (e ≥ 980: 1074 prunes) and L5 (e ≥ 1480: 12); on G the tail reaches L6 (343) but nothing at the capped L7 under CFD 6. **The depth limit is not what binds on O — the deficit slope is**; on G the depth limit takes the last 343 prunes away when CFD moves 6 → 5 (C2 vs C1: 50 rows move, no best move changes).

## 4.3 Findings
1. **Prediction scorecard**: (1a) largest L on O = 5 → KILLED, measured 3 (within my declared kill range "4 or lower"); (1b) share L ≤ 2 ≥ 60 % → HELD (88.9 %); (2a) largest L on G = 6 → HELD (343); (2b) share ≥ 50 % → HELD (71.9 %); (3) C5 and C6 differ from C4 on O → HELD (141/200 and 142/200 nodes equal, 4 and 3 best moves move); (4) plant zeros → HELD; (5) arithmetic zeros → HELD.
2. **The multiplier dominates the depth limit**: moving Multiplier 250 → 100 (C4 vs C1) changes 195 of 200 node counts on O and 282 of 353 on G; moving the depth limit by a whole ply (C2, C3) changes 0 rows on O and 25–50 on G, never a best move. If the tuner wants capture futility to matter, Multiplier and Base are the levers; Depth 5/6/7 is a fine trimmer at most. (Consistent with job 2's Part B.)
3. **The gate is arithmetically exact**: in 14 runs and ~2.6 M counted candidate events, gate_yes == pruned-total and bad_prune == 0 — the code prunes precisely the candidates its formula admits, no more, no less (with FORGE_MATE_ALPHA_GUARD compiled out; the guard text exists in the source but the flag is not defined in the default build — checked: the name appears only behind #if defined).
4. Suspicions, not proven: none new; the "deficit slope, not depth, binds on O" reading is a summary of the measured tables, not a code trace.

## 5. What I read from my colleagues
kimi5's job-12 report (its FailHighBlend numbers, recounted by Opus in file 3 as equal to the peer instance's job-3 report); file 3's account of the two-session situation. No colleague note bears on capture futility except job 2's own Part B.

## 6. What I did NOT do
Nothing asked. The two-session protocol from file 3 was followed: this is the lowest job file without a report under MY name (the peer instance's REPORT_deepseek6_job3.md covers the FailHighBlend testing; I did not redo it).

## 7. What I am NOT sure about
Whether `history` at the gate is the capture-history term or the quiet-history lookup for this move — I instrumented the SAME variable the gate reads, so the counts are self-consistent either way; naming it in the report would need a source trace I did not make.

## 8. A better way
The per-L deficit bins could be split pruned/unpruned to read the margin distribution directly at the gate; the candidate-wide bins already answer the job's question, so I did not add a second table.

## 9. times: see stamps.txt. One disclosed slip: I typed "2026-11-16T17:47:50Z" by hand into PREDICTION.md's second line instead of pasting `date -u` — the committed prediction (3db68a9c8) carries that typed line; stamps.txt holds the real commit-time stamp (2026-11-16T17:44:40Z, immediately before the commit). The typed time is close to but not the pasted output; noted here so the record stays honest.
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_job3b/counters.patch.txt
 M forge-combo29/tests_deepseek6_job3b/stamps.txt
?? forge-combo29/REPORT_deepseek6_job3b.md
?? forge-combo29/tests_deepseek6_job3b/c2c3_compares.txt
?? forge-combo29/tests_deepseek6_job3b/c4c5c6.txt
?? forge-combo29/tests_deepseek6_job3b/cfp_C0_C1.txt
?? forge-combo29/tests_deepseek6_job3b/cfp_C0_C1_C3.txt
?? forge-combo29/tests_deepseek6_job3b/cfp_C1_C3.txt
?? forge-combo29/tests_deepseek6_job3b/cfp_rest.txt
?? forge-combo29/tests_deepseek6_job3b/checks.txt
?? forge-combo29/tests_deepseek6_job3b/counterrun.py
?? forge-combo29/tests_deepseek6_job3b/job3b_runs.sh
?? forge-combo29/tests_deepseek6_job3b/runs/
?? forge-combo29/tests_deepseek6_job3b/step0.txt
?? forge-combo29/tests_deepseek6_job3b/sumcfp.py
$ ls forge-combo29/tests_deepseek6_job3b/
c2c3_compares.txt
c4c5c6.txt
cfp_C0_C1_C3.txt
cfp_C0_C1.txt
cfp_C1_C3.txt
cfp_rest.txt
checks.txt
counterrun.py
counters.patch.txt
job3b_runs.sh
PREDICTION.md
runs
stamps.txt
step0.txt
sumcfp.py
```
