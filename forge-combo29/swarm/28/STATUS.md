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
