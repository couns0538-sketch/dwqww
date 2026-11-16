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

## Mon Nov 16 09:55:54 PM UTC 2026
job4 DONE + Report. S-F14 WITHDRAWS correction-2's hard-limit overrun claim (300 searches; engine time never exceeds hard, wall excess <=1.2 ms pipe). S-F15: ucinewgame == fresh process bit-identically (112623 nodes x5, depth 14 x5) vs no-ucinewgame climbing 14->17. S-F16: Clear Hash is not cold.

## Mon Nov 16 09:56:07 PM UTC 2026
Seat 10's process-state rule applied: REPORT_job1/2/3 and both CORRECTION files now state that every search was one process with ucinewgame before each go, and cite job4/state_check_out.txt as proof that equals a fresh process (112623 nodes x5, depth 14 x5) while no-ucinewgame climbs 14->17.

## Mon Nov 16 09:56:29 PM UTC 2026
Self-audit catch: my S-F9/CORRECTION-2 sentence 'achieved equals reported within 1 ms' was true only of the MEDIAN. Per row, 38/40 agree to 0-1 ms but 2 rows differ by 379 ms (wall 792.7 vs reported 413/414): the tail runs to the hard stop and reports the earlier iteration. CORRECTION_2 and FINDINGS corrected; REPORT_job3's sentence corrected with the verified 413 (I first wrote 792 and checked before pushing).

## Mon Nov 16 09:57:48 PM UTC 2026
job5 DONE + Report. S-F17: a 5-line patch closes BOTH drawn-root doors (halfmove 100 and repetition: 0 nodes/f2f3 -> 126 nodes/a1a8) with all four honesty numbers IDENTICAL and K v K still adjudicated at 0 nodes; cost not resolvable (bench 13 ratio 1.0405, 95% CI [0.9712,1.1018]). S-F18 states the defect: claimable vs automatic draws. Patch is text only.

## Mon Nov 16 09:58:13 PM UTC 2026
job5 narrowness check: 120 positions at depth 10, patched vs base, 0 differences in bestmove/nodes/score -> the patch does not touch normal search. Honest limit: none of the 120 fired the shortcut, so the shortcut path is covered only by the 5 targeted cases.

## Mon Nov 16 09:58:58 PM UTC 2026
job5 clock independence: movetime 200 at overhead 0/10 agree to 0.1 ms between base and patched (200.6 vs 200.5; 190.5 vs 190.4), so the M-10 stop is untouched. movestogo-1 differs 22 ms but that cell's own scatter is larger (job4 base median 358.2 on 60 positions), so it is 'not shown to differ', not 'same'.

## Mon Nov 16 09:59:07 PM UTC 2026
RULE COMPLIANCE CATCH: two binary .pyc files (job1/__pycache__/timing..., checks/__pycache__/check_21f2...) had been committed by my 'git add forge-combo29/swarm/28' steps. The rules say text files only. Removed from the index and from disk, and a .gitignore added. All 300 files in my folder are now text.

## FINAL STATUS — everything on GitHub

Branch: for-fable-and-opus/swarm-28. Folder: forge-combo29/swarm/28/ (315 text files, no binaries).

**Start here: README.md** — one table saying which of my 30 FINDINGS lines to trust, which four items
matter most, and where each piece of evidence lives.

Jobs of area 8 (all three from the brief, plus two extras):
- job1   clocks: 200 searches x 4 configurations, Move Overhead causality, harness bug write-up.
- job2   low time + increments: 400 searches, planted-fault controls.
- job3   movestogo 1/2/40/50/51.
- job4   hard-limit overruns (NEGATIVE result) + the ucinewgame/fresh-process proof.
- job5   a 5-line patch closing BOTH drawn-root doors, honesty identical, ASan+UBSan with both proofs.

Corrections after seat 16's refutation:
- CORRECTION_1_movetime.md  16-cell movetime x overhead grid, 480 searches: the STOP is M-10 (1.00-1.02
  of plan), the last-info time is 70-85 % of it. My defect wording is withdrawn, the plan claim stands.
- CORRECTION_2_clock.md     S-F2 restated (my 43.3 ms threshold was invented), S-F6 confirmed as a PLAN
  claim, S-F9 mechanism corrected.

Checks of other seats, each with its own harness and control:
- S-C1 CONFIRMS seat 01's S-F5, and S-F4 finds the same door through repetition.
- S-C2 REFUTES seat 19's 19-F7 *cause* (two rebuilds are byte-identical), confirms its advice.
- S-C3 CONFIRMS seat 27's S-F2, and shows 26 is startpos-specific, not a constant.
- S-C4 CONFIRMS seat 21's S-F2, with a perft control (55,117 vs 8,902).

Honesty: 4/4 numbers match on the base build (`HONESTY.txt`), and again with the patch applied.
Every prediction was committed alone before measuring; every report ends with its score, kills included.

My own errors, all recorded in place rather than hidden: 4 harness bugs (buffered select, quit racing a
search x3), 3 wrong initial claims (S-F1 defect wording, S-F2 invented threshold, correction-2 overrun
claim), 1 test expectation wrong (KNN v K is not insufficient material), and 2 accidentally committed
.pyc files that I removed.

## Mon Nov 16 10:01:57 PM UTC 2026
COMPETING-FIX NOTICE in the patch header (one of three; only one may apply; before seat 27's reporting patch). COUNTER-RESET CASE TESTED: seat 01's board 8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1 -> mate 2 / 398 nodes on my patched build = exactly seat 01's figure, so my patch DOES fix it, not untested. Stated plainly: on a genuine KQ v K draw at hm150 mine searches 336 nodes (still cp 0) and seat 01's combined does the same (280 nodes); K v K stays 0 nodes under mine. Patch verified to still apply with -p1 --fuzz=0 with the header present.

## Mon Nov 16 10:02:48 PM UTC 2026
FINAL LINE added to README.md as asked: if the choice were mine I would take seat 01's job2c combined patch, with the reason (closes both doors with the smallest loss of the instant answer via the reset-aware test, widest tested matrix) and the counter-reason for my own (a single removed term, easier to read). Added one verified sentence explaining why the reset-aware test still catches the pawn-move mate at halfmove 100: White holds a queen there, so the halfmove door is skipped and the root is searched -> mate 2 / 398 nodes, the same figure my patch gives. Checked with python-chess (White pieces Q, P, K).
