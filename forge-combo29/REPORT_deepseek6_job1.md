# REPORT — deepseek6, job 1 (the 35 tuner settings, each moved by its own step under S14)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_job1/ · job clock started 2026-11-16T16:30:51Z (tests_deepseek6_job1_start.txt); report written 2026-11-16T16:44:10Z, minute 14 of 60.

## 1. Three lines

**Asked:** for each of the 35 settings the tuner moves, do the searches at value−c and value+c differ from S14 at all (Parts 0–3, controls first)?
**Answer:** Step 0, all three controls and Part 0 all MET (numbers below). The settings whose two runs equal S14 in nodes on all positions: **on O exactly three (QsSeeMargin, CaptureFutilityMultiplier, CaptureFutilityDepth); on G the same three; on both, the same three.** **64 of 70 runs differ from S14 on O; 64 of 70 on G** (the 6 equal runs are those three settings at both ends). Part 3 ran and all three +4c runs are exact identities too. My prediction ("exactly these three, count 3") was MET.
**How sure:** certain — every cell comes from a committed rows file + .meta pair, compared by one committed command; the controls' known answers were all reproduced exactly.

## 2. Honesty numbers (raw output in this folder)
Plain build /tmp/glmflash5_base/build/forge sha256 e06310eca3368556: honesty_bench11.txt 312866, honesty_bench13.txt 862329, honesty_bench16.txt 3024920, honesty_perft5.txt 4865609 — all four exact. Fresh S14 rows: O_S14.rows sum 9,500,069 (first three 41,311/24,872/28,574), G_S14.rows sum 18,466,239 (353 rows).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| Step 0 honesty + S14 rows | done | honesty_*.txt, O_S14.rows(.meta), G_S14.rows(.meta) | all four honesty numbers exact; sums 9,500,069 / 18,466,239 as known |
| Controls QsSeeMargin 0/99/100 | done | ctl_qsm0/99/100.rows(.meta) + compare_job1.py output in tabledump.txt | 0: sum 9,500,069, nodes 200/200, bm 200/200; 99: same; 100: sum 9,768,507, nodes 1/200, bm 173/200, first three 41,356/23,935/28,720 — all as the job states |
| Part 0 (NL release d10, def + nss48) | done | part0_nl_def.rows, part0_nl_nss48.rows + compare_part0.py output in tabledump.txt | release sums 3,809,466 and 3,640,772; vs my sanitizer rows: nodes equal 200 of 200 AND bestmove equal 200 of 200 for BOTH. The build does NOT change the tree; the sign flip was a matter of DEPTH, not build |
| Part 1 (70 runs on O) | done | p1_*.rows (70 files) + part1_table.txt | 64 of 70 differ in nodes somewhere; 6 equal (the three inert settings) |
| Part 2 (70 runs on G) | done | p2_*.rows (70 files) + part2_table.txt | 64 of 70 differ; the same three inert |
| Part 3 (+4c for the inert three) | done | p3_QsSeeMargin_64.rows, p3_CaptureFutilityMultiplier_350.rows, p3_CaptureFutilityDepth_10.rows | all three sums 9,500,069, nodes equal 200 of 200, bestmove equal 200 of 200 — still exact identities at 4 steps away |
| Prediction before first measuring run | done | prediction.txt, commit "deepseek6 job 1 prediction" (b52f64710) | predicted exactly those three, count 3 — met |

## 4. The table
Each cell from the rows file named by its pattern `p1_<setting>_<m|p>.rows` / `p2_...` in this folder; equality counts from compare_job1.py vs O_S14.rows / G_S14.rows (see tabledump.txt for the exact command output).

## 5. Findings
1. **QsSeeMargin is inert from 0 to at least 99** (controls at 0 and 99 identical to S14; 100 differs) — confirms kimi5's job-10 analysis on MY build, and 34/46/64 are all inside the band. Command: `python3 compare_job1.py ctl_qsm99.rows O_S14.rows`.
2. **CaptureFutilityMultiplier and CaptureFutilityDepth are fully dead at the default** — ±c AND +4c (350, 10) are exact identities on all 200 positions, because the capture-futility block (search.cpp:1893) only runs when CaptureFutilityBase > 0 (default 0). The tuner would read pure noise on both. Command: `python3 compare_job1.py p3_CaptureFutilityDepth_10.rows O_S14.rows`.
3. **SingularMargin is by far the strongest lever per step**: ±1 swings the O sum to 13,196,949 (+38.9 %) and 8,186,451 (−13.8 %) — larger than any other one-step move in the table.
4. **Six runs change nodes but never the best move on O**: NullMoveEvalDivisor both ends (131/144 nodes-eq, bm 200/200), RfpDepth both ends (79/140, bm 200/200), FutilityDepth −c (133, bm 200/200), FutilityBase/FutilityMultiplier ±c have bm 190–195. Only one run in the whole job changed a best move on O with a small step: FutilityDepth +c, bm 199/200.
5. Suspicions, not proven: the SeeValue-multiple-of-100 explanation of (1) is kimi5's/Opus's reading of board.cpp:24, which I did not re-derive from source; my evidence is the measurement alone.

## 6. What I read from my colleagues
Before this job (job-file rule 5, 2026-11-16T16:29:50Z): kimi5's NOTES tail (job-10 QsSeeMargin control, CaptureFutilityBase gate), glmflash5's cross-2 (353/353 equal remakes), deepseek5's notes tail. Nothing contradicts this report; glmflash5's NullStaticSlope-48 G sum 6,400,760 matches my long-8-addendum number.

## 7. What I did NOT do
Nothing from the job file. All of Steps 0, controls, Part 0, Parts 1–3 done. (Part 0's "one sentence": the build does not change the tree — release d10 and sanitizer d10 are bit-identical row for row — so the sign flip is a matter of depth; from now on I write "depth", not "depth or build".)

## 8. What I am NOT sure about
Nothing material. Note for the table reader: "nodes-equal" counts compare the NODES column only, per the job's definition; bestmove-equal counts are in their own columns.

## 9. A better way
Run the 35 settings' two ends as ONE engine process each with MultiPV-style batching — not possible in this protocol; the per-position ucinewgame is what makes rows comparable, so no change.

## 10. times: see stamps.txt  ·  model name: glm-5p3-flash
