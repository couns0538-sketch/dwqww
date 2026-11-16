# STATUS — swarm seat 28

- seat: 28
- branch: for-fable-and-opus/swarm-28
- area: 8 (THE CLOCK)
- seed: 2801

## 2026-11-16T21:05Z
Seat claimed (SEAT.txt committed by take_seat.sh). Next: STEP 2 build of 6b98f217 + honesty check.

## Mon Nov 16 09:14:00 PM UTC 2026
job1: harness bug found+fixed (README_HARNESS_BUG.md). mt50 x2 + mt500 done, 200 searches each, 0 non-ok.
movetime 50 -> median 40.5 ms (10 ms UNDER budget); movetime 500 -> median 490.6 ms (9.4 ms under).
running: wt1000, wt10000 in tmux swarm28-timing.

## Mon Nov 16 09:18:05 PM UTC 2026
job1 DONE. REPORT_job1.md written. Findings S-F1..S-F3. Prediction 9/15 survived, 6 killed (all in the same direction: the engine does not follow the budget it is given).

## Mon Nov 16 09:19:09 PM UTC 2026
CYCLE 1: checked seat 01's S-F5 -> S-C1 CONFIRMS (exact numbers). Found S-F4 beside it (repetition term of the same expression).

## Mon Nov 16 09:21:20 PM UTC 2026
job2 DONE. REPORT_job2.md. Findings S-F5 (increment ignored below Move Overhead), S-F6 (hard limit excludes increment), S-F7 (wtime 0 answers legally), S-F8 (0 overruns in 400 low-time searches). Prediction 10/13.

## Mon Nov 16 09:26:45 PM UTC 2026
Rule 1 from FABLE_TO_swarm_2 applied to my zeros: job1 (no-NORESP, no-overrun) and job2 (400/400 legal, 0 over wtime) each broke a planted fault 8/8 and 400/400, real engine 0. Files job2/out_plant*/ , plant_verdict*.txt. Both REPORTs updated.

## Mon Nov 16 09:27:42 PM UTC 2026
job3 DONE. REPORT_job3.md. S-F9 (movestogo 1 uses 32% of clock = 65% of its own soft plan), S-F10 (clamp at 50 exact), S-F11 (0 overruns). Prediction 7/10.

## Mon Nov 16 09:29:48 PM UTC 2026
CYCLE 2: checked 19-F7 -> S-C2 REFUTES its cause (build-to-build) but CONFIRMS its advice. Two clean rebuilds are byte-identical (sha256 e06310ec...); alternating them 12x gives 0.45 % between builds vs 8-17 % within one build. Also corrected my own S-F3 with S-F12.

## Mon Nov 16 09:30:57 PM UTC 2026
CYCLE 3: checked 27-F2 -> S-C3 CONFIRMS exactly (threshold 26 at startpos). Beyond it S-F13: the book does not answer startpos at all on this build (Book File empty), and the node threshold is one root iteration, not the constant 26 (a 51-move position switches between 40 and 60).

## Mon Nov 16 09:34:48 PM UTC 2026
CHECKPOINT PUSH requested by owner. Jobs 1-3 of area 8 done; checks S-C1 (confirms 01-F5), S-C2 (refutes 19-F7 cause), S-C3 (confirms 27-F2) pushed. 21-F2 check RUNNING now (pid 13306) - it stalls on a wrong perft wait token; will be killed and fixed next. Branch tip dc466c682 before this block.

## Mon Nov 16 09:37:55 PM UTC 2026
CORRECTION 1 PUSHED. S-F1 re-tested: seat 16 was right that the last-completed-iteration confound is real, but the STOP is the plan (50.5 ms at overhead 0, 40.5 at overhead 10, 25.4 at 25, 5.4 at 45). My defect wording withdrawn; the M-10 plan claim stands. 480 searches, 16 cells, 0 NORESP, integrity audit passes on all 19 raw files.

## Mon Nov 16 09:39:54 PM UTC 2026
CORRECTION 2 PUSHED. S-F2 restated narrower (my 43.3 ms threshold was invented; against the engine's own plan: 54 over soft, 0 over hard). S-F6 confirmed and now a claim about the PLAN (plan soft 822 vs 117 ms at equal total clock). S-F9 numbers stand but mechanism corrected (achieved==reported within 1 ms, so it is a target undershoot); NEW: 2/40 movestogo-1 searches exceeded the engine's own hard plan.

## Mon Nov 16 09:40:05 PM UTC 2026 CHECKPOINT (owner: findings on GitHub by 22:30)
Everything is pushed. Complete inventory:
- HONESTY.txt: 4/4 match (312866 / 862329 / 3024920 / 4865609), exe sha256 e06310ec...
- job0..job3: area-8 jobs 1,2,3 all DONE with REPORT_job1/2/3.md, raw per-search TSVs, predictions committed alone, prediction scores.
- correction/: CORRECTION_1_movetime.md (16-cell grid, 480 searches) + CORRECTION_2_clock.md (S-F2/F6/F9 re-check) + audit_timestamps.py (19 files, 0 problems) + verify_wall_is_the_stop.py.
- checks/: S-C1 (CONFIRMS 01-F5 + new S-F4 repetition door), S-C2 (REFUTES 19-F7 cause), S-C3 (CONFIRMS 27-F2 + S-F13).
- FINDINGS.md: 20 lines + a reading guide mapping each superseded original to its REVISED line.
- Rule 1 planted faults: job2/out_plant*/ (illegal 400/400, overrun 400/400, noanswer 8/8; real engine 0).
Branch tip before this block: ce87c538c.

## Mon Nov 16 09:45:12 PM UTC 2026
CYCLE 4: S-C4 CONFIRMS 21-F2 with a perft control (55117 vs 8902). Two more of my own harness bugs found and fixed (perft prints 'nodes' not 'Nodes searched'; ucinewgame prints no readyok) - both recorded in the check.
