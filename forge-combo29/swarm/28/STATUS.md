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

## Mon Nov 16 10:19:01 PM UTC 2026 CONTINUE: 12 more hours, ends at 2026-11-17T10:19:01Z
Assignment: read every unread FABLE_TO_swarm_N.md from lowest N up; build the PC engine from FABLE_TO_swarm_5 (patch against 6b98f217, -DFORGE_MATE_ALPHA_GUARD=1, in a SEPARATE copy); re-run 08-F11 and my drawn-root results on the PC build under PC20 before anything else; then THE CYCLE with both builds.

## Mon Nov 16 10:20:01 PM UTC 2026
PC BUILD READY. Patch sha256 d6bd72c531f785f4... MATCHES the expected prefix; 11 files, zero fuzz; built with -DFORGE_MATE_ALPHA_GUARD=1 at ~/build/pc-r15 (exe 068f0927768d30be). ALL published numbers reproduced: pins default 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276 — every one MATCH. Also read FABLE_TO_swarm_3 and _4: file 3 says my drawn-root findings are REPAIRED on the PC and a base-tree patch is not needed; file 4 says pins are default-option and sums are S14, which my job0 harness conflated. Next: re-run 08-F11 and my drawn-root results on the PC build under PC20.

## Mon Nov 16 10:21:49 PM UTC 2026
SWARM THREADS RULE applied. THREADS_AUDIT.md: 08-F11's base numbers came from seat 08's harness which DID send Threads 1 explicitly (their job5/raw/.meta); my 10 search harnesses all send Threads 1 explicitly except pcbuild/pins.py, which must not (pins are default-option per file 4, and the default IS 1). Score reproducibility measured: Threads 1 identical 5/5 (e1g1, cp 54, 27066 nodes); Threads 4 gives 5 distinct scores, 5 distinct node counts AND 2 distinct moves - so I reproduce seat 04 and extend it (the move varies too). S-F20: 08-F11 re-tested on PC r15/PC20 - tail shape reproduces (p99/median 2.20-4.43) but absolute p99 is 1.5-1.8x lower than base and 0/120 searches exceeded its clock.

## Mon Nov 16 10:22:00 PM UTC 2026
DRAWN-ROOT re-run on PC r15 / PC20 / Threads 1 / depth 12: ALL REPAIRED, exactly as FABLE_TO_swarm_3 says. hm99/hm100/hm150 and third-repetition all search and find a1a8 / mate 1 (252/252/252/240 nodes) vs base 0 nodes/f2f3; seat 01 counter-reset board gives mate 2 / 398 nodes; K v K still 0-node shortcut. S-F5, S-F4, S-F17, S-F18 are BASE-TREE ONLY - my patch must NOT be applied to the PC tree. (S-F23)

## Mon Nov 16 10:22:35 PM UTC 2026
TASK 1 DONE: DRAWN_ROOT_DOORS.md - per-door base vs PC20 side by side with node counts, one sentence at the top saying no drawn-root patch from this swarm is needed on the PC tree. All 4 doors: base 0 nodes/cp 0/f2f3 -> PC20 240-398 nodes with mate score. Controls unchanged (K v K still 0 nodes; KQ v K still cp 0). A first run of the script reported A3 as STILL BROKEN because my judge tested for immediate checkmate and mate 2 is not immediate - fixed to judge by score, and that wrong verdict was corrected before anything was written up.

## Mon Nov 16 10:24:26 PM UTC 2026
TASK 2 DONE, and it went AGAINST my prediction (S-F25). Same grid both builds, Threads 1 each, 16 pos/cell, achieved time + last depth: wtime 1000 PC same depth 13 in 36% less wall; wtime 3000 same depth, same time; wtime 10000 PC depth 18 vs base 20 in 12% less time. nps is NOT higher on PC (1.02x / 0.87x / 0.90x). So S-F20's better tail = STOPS EARLIER, not deeper searching — and at the long clock it costs 2 ply. V2/V3/V6 refuted. This reframes S-F20 from a strength claim to a time-management difference; will verify with more positions before stating it as final.

## Mon Nov 16 10:26:33 PM UTC 2026
S-F25-REVISED after 40 positions/cell (the 16-position sample understated noise): 'stops earlier' is clear ONLY at wtime 1000 (same depth 13, wall 0.88x). At 3000 no separation (same depth, 1.09x); at 10000 PC depth 19 vs base 20 at 0.89x. nps comparable (1.08/0.91/0.94). Conclusion: the PC build has NO per-node speed or depth advantage here; its smaller tail is a short-clock effect costing ~1 ply at 10 s. So S-F20 is 'less time at short clocks', NOT 'stronger search'.

## Mon Nov 16 10:26:43 PM UTC 2026
README status table extended: it had stopped at S-F19 (S-F19 itself was missing). Now covers S-F19 through S-F25-REVISED, marking S-F20 as narrowed and S-F25 as superseded. 26 rows.

## Mon Nov 16 10:29:38 PM UTC 2026
S-F26: the 10 s lost ply CAUSE FOUND and it is not the plan. All five plan inputs have identical defaults on both builds (read from each exe's uci answer), so soft=454/hard=2270 at wtime 10000 on BOTH. The difference is the STOP: PC20 stops at 0.68 of soft (311 ms, depth 19) vs base 0.77 (349.7 ms, depth 20). Ladder: median last-iteration finish 287 vs 376 ms at 1.25x growth per iteration, so 89 ms earlier stopping = exactly one ply. Since the arithmetic is identical, the cause is in the stop logic where FORGE_FIX_HARD_LIMIT_EMERGENCY lives: a fixable constant, not search quality. Stated in LADDER_README.md that my budget_left.py projection is a HEURISTIC (growth varies 0.30x-5.60x) and is an indication, not a count of wasted ms.

## Mon Nov 16 10:34:59 PM UTC 2026
S-F27: S-F26's CAUSE RESOLVED. The stop-decision source is BYTE-IDENTICAL between builds (diff = 0 lines; all 11 relevant defaults equal). Proof by turning switches off on the SAME binary: PC r15 with all five PC20 switches OFF reproduces base exactly (0.784 vs 0.769 of soft, 20 iters, depth 20); with them ON it is 0.633 / 19 / depth 19. So the lost 10 s ply is a SWITCH-POLICY trade-off, not a bug and not a constant: HistRework/TtPruneV2 shrink the tree so PC20 visits 26% fewer nodes in 17% less time (node rate 11% LOWER) and fewer iterations fit before soft expires. FORGE_FIX_HARD_LIMIT_EMERGENCY is NOT the cause. Nothing patched. Written in pc20/STOP_CAUSE.md. Noted honestly that the switches are NOT independent: HistRework-off and TtPruneV2-off each restore 20 iters but together give 0.671, so 'the switch set' is the answer, not one culprit.

## Mon Nov 16 10:38:46 PM UTC 2026
S-F28: the lost ply is COSMETIC and the control proves it. ASKED NUMBER: PC20-clock vs base-depth20 on the 16 shallower positions = 75.0 % (12/16). CONTROL: base-clock vs base-depth20 on the same = 87.5 % (14/16). DECISIVE: at EQUAL fixed depth the builds agree only 72.5 % (29/40) at d20 and 80.0 % (32/40) at d19 — MORE disagreement than the ply case, bigger sample. So the switch set changes moves at equal depth and the ply contributes nothing measurable. Reported plainly that agreement is not strength and that 27.5 % move change at equal depth needs a match, not more measurement. Six spot-checked disagreement pairs score 276-vs-1279, 0-vs-23, -3015-vs-3737, 43-vs-19, -351-vs-308, 533-vs-718 cp — not tie-breaks. Also caught my 5th quit-during-search harness bug before using any number from it.

## Mon Nov 16 10:40:22 PM UTC 2026
S-F29: the 11 equal-depth disagreements re-searched deeper (base build judging both moves at depth 18, White-relative): BASE better in 6, PC20 better in 2, equal 3 (median gap 33 cp, max 221). Mixed, leaning base - no clean pattern. Excluding the two decided +-100000 rows the informative split is base 6 / PC20 2 / equal 1. Not claiming strength. A control caught TWO real sign bugs in my judge before any number was used (checkmated side reported as 'mate 1'; mate 0 mapped to score 0) - fixed and re-verified. Read FABLE_TO_swarm_6: ply thread closed officially; next priority is re-running the tail/stop work at the owner's REAL control, 6 s + 0.06/move.

## Mon Nov 16 10:42:32 PM UTC 2026
OWNER'S REAL CONTROL (6s + 0.06, PC20, Threads 1, Hash 16) DONE - S-F30/S-F31. Bimodal tail: 5 of 120 searches spend 1.2-1.59 s of a 6 s clock (20-26% of the game's initial time). p99/median 5.7x/6.6x vs my 2.2-4.4x without increment - Y6 killed. Worst case deterministic: 8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w gives exactly 1585 ms (hard plan) on 3 runs, identical nodes, but its last COMPLETED iteration ended at ~1020 ms - so it ran ~565 ms more and completed nothing. Stop fractions base 0.78 / PC20 0.71 reproduce S-F27 at the control that matters. NOTE: found my own data defect (rows written before FEN recorded, 60/60 empty), fixed and re-ran the whole job.

## Mon Nov 16 10:44:35 PM UTC 2026
S-F32: soft-scaled rule arithmetic (no new experiment). FREE on 15/24 base and 18/24 PC20 (zero plies lost), buys 300-1240 ms on the tail for 1-3 plies; biggest single win 1239 ms for 1 ply. Stated plainly: ladders are at wtime 10000 (soft 454) not the 6 s control, so ms do not transfer directly, ratios do. Also recorded that heavy searches are build-AND-position dependent: base#7 is 1585 on base vs 843 on PC20, pc#57 is 281 on base vs 1586 on PC20 - the tail board differs by build, consistent with S-F27.

## Mon Nov 16 10:45:02 PM UTC 2026
S-F33 softnodes DONE (short, as promised): DETERMINISTIC at every N (5 repeats x 3 positions, identical nodes/depth/move), ALWAYS stops at a finished depth, overshoot 1.02x-1.99x and the ratio GROWS with N (1.02-1.59 at 2k, 1.24-1.99 at 250k). Owner's 'first depth after 2000 nodes' is literally true; but a 250k softnodes search can spend nearly 2x the stated budget, so a match control treating it as a hard cap is wrong. 4N cap never fired.

## Mon Nov 16 10:45:49 PM UTC 2026
S-F34 gated rule measured. RECOMMENDATION: adopt G=1.5 (stop only when projected finish exceeds soft by >=1.5x that iteration's own cost). On PC20 it removes EVERY 2+ ply loss (4->0) while keeping mean 35 ms / max 424 ms saving; the gate sweep has a clean knee at 1.5. Ungated: 85 ms mean / 826 max at up to 4 plies. CAVEAT IS IN THE RECOMMENDATION ITSELF: ms measured at the 10 s plan (soft 454) - ratios transfer to the 6 s clock, milliseconds do not. Hand-checked the rule arithmetic on a synthetic ladder. Not a strength claim; computed from ladders, so the real implementation's cost estimate is the adoption risk.

## Mon Nov 16 11:15:55 PM UTC 2026
Hourly check received. Clock thread (S-F26..S-F38) is closed. Now starting the per-move p90 measurement at 6s+0.06 on REAL GAME positions, as asked: median 105 ms against a 60 ms increment means each move loses clock and the tail decides when it runs out. Plan: simulate a REAL COUNTDOWN (not a constant 6000 ms clock, which I showed inflates the tail - constant gave 1585 ms outliers, countdown gave max 828 ms), play actual games engine-vs-engine at 6s+0.06 under PC20 Threads 1, record every move's search time and the clock trajectory, and report median/p90/p99/max plus whether and when a clock flags.

## Mon Nov 16 11:18:30 PM UTC 2026
S-F39 per-move p90 at the owner's control measured ON REAL GAMES: 4 games, 281 moves, real countdown. median 132 ms, p90 359 ms, p99 550, max 608 ms; 275/281 moves (98%) exceed the 60 ms increment so the clock falls almost every move; 0 of 4 flagged, all repetition draws at 58-101 plies. p90/max far below my constant-clock 1585 ms figure - another confirmation that a constant clock inflates the tail. Limits: self-play draws end early so these games never probe the long-game regime; extrapolation says the clock lasts ~83 moves/side at the median, ~20 at the p90.

## Mon Nov 16 11:21:17 PM UTC 2026
S-F40 longer games (6, different openings): median 99 ms, p90 262 ms, max 792 ms; longest game 224 plies with a side holding ~115 ms for 37 consecutive moves and its depth falling to 10-12 - the time manager self-limiting correctly. 0 of 6 flagged, but 2 games ended with a side under 300 ms and from 111 ms one more p90 search would flag. Combined with S-F39: 1,090 moves, median 99-132, p90 262-359, max 792. THE ANSWER: the clock survives at 6s+0.06, the margin at long games is about one p90 move.

## Mon Nov 16 11:21:54 PM UTC 2026
S-F41 RETRACTS my own transition mechanism. Constructed the case as asked (4 complex middlegames x clock 300/200/150/111, 16 searches): ZERO flagged, and the walls (22-50 ms) were far below even the hard plan (60-174) because the engine finishes its ladder early. And the arithmetic says it must be so: hard = min(available*60/100, soft*5) means a search can never spend more than 60% of the remaining clock, so hard < clock+60 at EVERY clock size. S-F39/S-F40's numbers stand; the 'one p90 move from flagging' interpretation does not. Correct statement is STRUCTURAL not adaptive: spending is proportional to what remains. Written in TRANSITION_REFUTED.md.

## Mon Nov 16 11:22:37 PM UTC 2026
S-F42 structural result, as asked: spend <= hard <= clock - MoveOverhead < clock + increment for EVERY overhead and increment, so the margin is overhead+increment (70 ms at the owner's control) at EVERY clock size - and it follows from the final clamp alone, independent of the 60%/80% constants. Spend is proportional to what remains. RESIDUAL RISK kept in the file as three items: (1) plan violation, (2) stall outside the search (the real one; machine/GUI not engine), (3) refused position -> unintended board. Written in CLOCK_CANNOT_BE_LOST.md.

## 2026-11-16T23:23Z INVENTORY (not the final block) — every find of seat 28, with state, build and settings

> **THE ONE CLOCK SENTENCE:** the risk margin is `MoveOverhead + increment` = **70 ms at the owner's
> control, at every clock size** — spend is capped at `clock - MoveOverhead` and a flag needs more than
> `clock + increment`, so the clock cannot be lost to the engine's own search.

> **This is not the FINAL block.** The 12-hour window closes at 2026-11-17T10:18Z; this inventory was
> written at 23:23Z because the three residual clock risks were asked to be kept in a summary block.
> The real `## <time> FINAL` block will be added at the end of the window, and it will reflect whatever
> changes between now and then. The content below is accurate as of 23:23Z.

Branch `for-fable-and-opus/swarm-28`. Folder `forge-combo29/swarm/28/`. **Start at README.md**, then
`DRAWN_ROOT_DOORS.md` (drawn-root decision) and `CLOCK_CANNOT_BE_LOST.md` + `GATED_SOFT_STOP_RULE.md`
(the clock results). All 55 FINDINGS lines are listed below; where a line was superseded the REVISED line is
the one to read and the original is kept so the trail is visible.

Builds: **base** = commit 6b98f217, Release GCC 13.3.0, exe sha256 `e06310ec…16a83` (all four honesty pins
matched). **PC r15** = FABLE_TO_swarm_5 patch, sha256 `d6bd72c531f785f4…` verified, 11 files zero fuzz, built
with `-DFORGE_MATE_ALPHA_GUARD=1`, exe `068f0927768d30be…`; all published pins reproduced (default
312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276).
Settings: **S14** = the 14 brief settings. **PC20** = S14 + CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false. Threads 1 and Hash 16 everywhere unless stated.

### Clock findings (area 8)

| id | subject | state | build | settings |
|---|---|---|---|---|
| S-F1 | `go movetime M` plans M − MoveOverhead | **superseded by S-F1-REVISED** | base | S14 |
| S-F1-REVISED | 16-cell grid: the STOP is M−O to 1-2 ms (wall/plan 1.00-1.02 in 15 of 16 cells); the reported time is 70-85 % of it | stands, my defect wording withdrawn | base | S14 |
| S-F2 | 41 % of 1 s-clock searches past `wtime/30+winc` | **superseded by S-F2-REVISED** (that threshold was mine, not the engine's) | base | S14 |
| S-F2-REVISED | against the engine's own plan: 54/200 over soft, 0/200 over hard | stands | base | S14 |
| S-F3 | movetime-50 wall reproducible to 0.05 ms | stands, narrowed by S-F12 | base | S14 |
| S-F5 | below Move Overhead the engine ignores a Fischer increment (`wtime 5 winc 1000` → 0.29 ms, depth 1) | stands | base | S14 |
| S-F6 + S-F6-REVISED | the hard limit excludes the increment; stated as a PLAN claim (soft 822 vs 117 ms at equal 2600 ms) | stands (revised wording) | base | S14 |
| S-F7 | `wtime 0` answered at once with a legal move | stands | base | S14 |
| S-F8 | 0 overruns in 400 low-time searches, with planted-fault control | stands | base | S14 |
| S-F9 + S-F9-REVISED | movestogo 1 uses 32 % of the clock; mechanism is a target undershoot, medians 323 vs 322 reported, 2/40 rows 379 ms apart | stands (revised mechanism) | base | S14 |
| S-F10 | `movestogo` above 50 clamps to exactly 50 | stands | base | S14 |
| S-F11 | no movestogo case overran the clock | stands | base | S14 |
| S-F20 | 08-F11 re-tested on the PC build: tail shape reproduces, absolute p99 1.5-1.8x lower | stands, magnitude refined by S-F25-REVISED | PC r15 | PC20 |
| S-F21 | Threads-4 score non-reproducibility reproduced AND extended (the MOVE varies too) | stands | PC r15 | PC20 |
| S-F22 | Threads audit: 10 of my 11 search harnesses send Threads 1; `pins.py` must not | stands | base | S14 |
| S-F25 + S-F25-REVISED | the PC tail is NOT deeper search — a short-clock effect costing ~1 ply at 10 s | stands (revised magnitude, 40-position sample) | PC r15 | PC20 |
| S-F26 | the 10 s lost ply is NOT the plan (all 11 defaults identical); it is the stop | stands | PC r15 | PC20 |
| S-F27 | the cause is the PC20 SWITCH SET — proven by turning all five off on the same binary (0.784 vs 0.769 of soft) | stands | PC r15 | PC20 |
| S-F28 | the lost ply is cosmetic: equal-depth disagreement (72.5 %) EXCEEDS the ply effect | stands | PC r15 | PC20 |
| S-F29 | of 11 equal-depth disagreements, deeper neutral re-search finds BASE better 6, PC20 better 2, equal 3 | mixed, no pattern; thread closed | PC r15 | PC20 |
| S-F30 | at the owner's 6+0.06 control with a CONSTANT clock the tail is bimodal, 5/120 searches at 1.2-1.59 s | stands — but see S-F40: a constant clock inflates the tail and is not the realistic harness | PC r15 | PC20 |
| S-F31 | the worst case is deterministic: 1585 ms at the hard plan while its last completed iteration ended at ~1020 ms | stands | base | S14 |
| S-F32 | soft-scaled stop rule is FREE on two thirds of positions, 1-3 plies on the tail | stands (arithmetic, 10 s ladders) | PC r15 | PC20 |
| S-F33 | `softnodes N` deterministic, always stops at a finished depth, overshoot 1.02x-1.99x growing with N | stands | PC r15 | PC20 |
| S-F34 | **gated rule, G = 1.5**: removes every 2+ ply loss on PC20, keeps 35 ms mean / 424 ms max | **recommendation**, see `GATED_SOFT_STOP_RULE.md` | PC r15 | PC20 |
| S-F35 | naive next-iteration predictor is poor (58 % median error) but the gate still agrees with the oracle 100 %, incl. out of sample | stands | PC r15 | PC20 |
| S-F36 | `c_last > soft` handled by ALGEBRA (G > C); limit: only 3 of 10 overruns preventable from a boundary | stands | PC r15 | PC20 |
| S-F37 | mid-iteration abandon: FREE for discarded iterations (578-936 ms), 1 ply for completing ones | stands | PC r15 | PC20 |
| S-F38 | Case B implementable: the abort path already publishes partial results (search.cpp:2439-2451), so gate on "no depth completed since soft" | stands, read from source | base | S14 |
| S-F39 | real games at 6+0.06: median 132 ms, **p90 359 ms**, max 608, 0 flags in 4 games | measurements stand; its flagging MECHANISM retracted by S-F41 | PC r15 | PC20 |
| S-F40 | 6 longer real games: median 99 ms, **p90 262 ms**, max 792, 0 flags; combined 1,090 moves | measurements stand; mechanism retracted by S-F41 | PC r15 | PC20 |
| S-F41 | **RETRACTS** the "one p90 move from flagging" mechanism: a clock search cannot flag, constructed case 0 of 16 | retraction, my error | PC r15 | PC20 |
| S-F42 | **the clock cannot be lost to a search**: `spend <= hard <= clock − MoveOverhead < clock + increment`, margin = overhead + increment at every clock size | stands — the result to hold | both | any |

### Drawn-root findings (base-tree only — repaired on the PC)

| id | subject | state | build | settings |
|---|---|---|---|---|
| S-F4 | the 0-node root shortcut also fires on `board.is_repetition()` | base-tree only | base | S14 |
| S-F17 | a 5-line patch closes both doors, honesty identical, ASan+UBSan clean | base-tree only, one of THREE competing fixes | base | S14 |
| S-F18 | the defect's shape: claimable draws treated like the automatic one | explanation only | base | S14 |
| S-F19 | three competing fixes; the counter-reset case does NOT separate them | stands | base | S14 |
| S-F23 | **all drawn-root findings repaired on PC r15/PC20** — no patch needed on the PC | stands | PC r15 | PC20 |
| S-F24 | `DRAWN_ROOT_DOORS.md`, the decision file | stands | PC r15 | PC20 |

### Method findings

| id | subject | state | build | settings |
|---|---|---|---|---|
| S-F12 | corrects my own S-F3: bench timing is NOT reproducible (8-17 % between single runs) | stands | base | S14 |
| S-F13 | the book does not answer startpos on this build (`Book File` empty) | stands | base | S14 |
| S-F14 | WITHDRAWS correction-2's claim that clock searches break the hard limit | withdrawn | base | S14 |
| S-F15 | `ucinewgame` restores the fresh-process state exactly; omitting it lets depth climb 14→17 | stands | base | S14 |
| S-F16 | `Clear Hash` is NOT a cold restore | stands | base | S14 |

### Checks of other seats' findings (each with its own harness and a control)

| id | subject | state | build | settings |
|---|---|---|---|---|
| S-C1 | CONFIRMS seat 01's S-F5 (halfmove-100 mate missed; exact 126→0 nodes), plus S-F4's repetition door | stands | base | S14 |
| S-C2 | REFUTES seat 19's 19-F7 *cause* (two rebuilds are byte-identical); its advice stands | stands | base | S14 |
| S-C3 | CONFIRMS seat 27's S-F2 (`go nodes` below one iteration); threshold 26 is startpos-specific | stands | base | S14 |
| S-C4 | CONFIRMS seat 21's S-F2 (refused FEN leaves the stale board) with a perft control 55,117 vs 8,902 | stands | base | S14 |

### Residual risk on the clock (kept here as asked)
A side can still flag only if one move's TOTAL wall time exceeds `clock + increment`, which the search cannot
do. The three ways: **(1) a plan violation** — the engine exceeding its own `hard` (a time-manager bug; not
seen in 1,090 measured moves); **(2) a stall outside the search** — scheduling, GUI latency, an OS pause
(the real risk at the owner's control, and a property of the machine and GUI, not the engine); **(3) a refused
position** — a bad FEN or illegal move leaves the previous board (S-C4), so the engine may search a board the
GUI did not intend.

### Honesty statement
Every table in every file is the pasted output of a committed script. Every prediction was committed and
pushed ALONE before its first measurement, and every report ends with its score including every killed
prediction. My own errors are recorded in place rather than hidden: five harness bugs (a buffered `select`,
and the quit-during-search trap five times), four wrong initial claims (S-F1's defect wording, S-F2's invented
threshold, correction-2's overrun claim, S-F14), one wrong test expectation (KNN v K), two accidentally
committed `.pyc` files removed, and S-F41's retracted mechanism.

## Mon Nov 16 11:22:56 PM UTC 2026
Note on the previous block: it is labelled INVENTORY, not FINAL. The 12-hour window closes at 2026-11-17T10:18Z, so a premature FINAL would be misleading; I wrote the inventory because the three residual clock risks were asked for as a standalone block, and I will add the real FINAL at the end of the window. Continuing with confirming.

## Mon Nov 16 11:27:28 PM UTC 2026
S-C5 CONFIRMS seat 05's S-F49 ranking on my own boards: depth order monotone on all 3 (softnodes 7 < 20k 10-11 < 50k 12-13 < 250k 15-16 < clock 18-19 < movetime 25-28), clock row reproduces depth 18 exactly. REFINEMENT to its contention caveat: 3 solo vs 3 loaded runs gave IDENTICAL depth 18 / 998,994 nodes / same move, only wall varied 589-647 ms - so the variation seat 05 saw is a SEVERE-contention effect, not general fragility, because a clock search stops at a completed iteration and its node count is a step function. Also noted my deep board needed ~1M nodes, above their stated 300k-780k range, so that range is board-dependent.

## Mon Nov 16 11:27:55 PM UTC 2026
Both items done. (1) THE MARGIN is now the first thing in three files (CLOCK_CANNOT_BE_LOST.md, README.md, the STATUS inventory block): the risk margin is MoveOverhead + increment = 70 ms at the owner's control, at EVERY clock size, because spend <= clock - MoveOverhead and a flag needs > clock + increment. (2) The contention test is promoted from a caveat-refinement to S-F43 in its own right: identical depth 18 / 998,994 nodes / same move in 3 solo and 3 loaded runs, only wall moving 589-647 ms; a clock search stops at a completed iteration so its node count is a STEP FUNCTION, meaning the control is quantised not fragile and a stressed run measures a lower rung of the same ladder.

## Mon Nov 16 11:29:36 PM UTC 2026
S-C6: checked seat 15's 15-F35 and found it CONFLICTS with my S-F42, so this is a resolution. CONFIRMS its measurements (36 games, 0 forfeits; my 113-ply game: min clock 117 ms, 0 forfeits) and REFUTES its prediction that a ~165-ply game would forfeit. Its arithmetic assumes a CONSTANT 73 ms drain; the real drain is hard(clock)-increment and hard scales with the clock, so iterating the real rule converges to a FIXED POINT of 111 ms from ANY starting clock (6000/3000/1000/500/300/200 all -> 111), analytically exact since hard=60 needs (clock-10)*0.6=60 -> clock=110. Seat 15's own 'per-move cost falls in the endgame (217->83)' is the visible half of that mechanism, not luck.

## Mon Nov 16 11:30:15 PM UTC 2026
S-F44 the fixed-point floor, written up as its own result for the FINAL: floor = MoveOverhead + increment*100/TmHardPercent = 10 + 3600/60 = 110 ms; iterating the real rule converges to 111 ms from ALL SEVEN starting clocks (6000/3000/1000/500/300/200/150), so the clock stops falling and no game length can forfeit by searching. Two precisions added while deriving it: (a) 111 ms is the WORST case - typical spend is nearer soft (~72 ms at 6 s vs a 60 ms increment) so real games settle higher, matching my measured 111-120 and 174-300 ms; (b) the cap is a BOUND not a target, PROVEN by setting TmHardPercent 30/45/60 at clock 600: caps 177/266/354 but measured spends 86/86/34 - the engine stops at soft inside the cap. CAVEAT CORRECTED while writing it: the floor does NOT depend on TmSoftDivisor or TmIncrementPercent (their term cannot bind here); it depends on MoveOverhead, the increment and TmHardPercent, and raising TmHardPercent LOWERS the floor (90 -> 77 ms).
