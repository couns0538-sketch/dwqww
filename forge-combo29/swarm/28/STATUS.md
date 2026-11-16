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
