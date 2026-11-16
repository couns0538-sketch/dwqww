## 2026-11-16T21:10Z
seat: 16
area: 6 (SYMMETRY)
branch: for-fable-and-opus/swarm-16
seed: 1601
- STEP 1 done: seat claimed, SEAT.txt pushed.
- next: STEP 2 engine build (worktree ../base) + honesty check.

## 2026-11-16T21:08Z
- STEP 2 done: release build at /home/ubuntu/builds/bld-release/forge, sha256 e06310ec..., id name "Chess Engine Forge 6.4.24 candidate".
- HONESTY 4/4 equal (312866 / 862329 / 3024920 / 4865609).
- next: THE CYCLE step 1 (read board) then area 6 job 1.

## 2026-11-16T21:14Z
- job1 (area 6) done: static `eval` of 353 G + 500 R positions vs python-chess colour mirror →
  853/853 identical in hce, nnue and total; controls: self 0 diffs, three true pairs 0 diffs,
  forced asymmetry 3 fields differ (harness can see a difference).
- files: job1/, REPORT_job1.md, FINDINGS.md (empty, negative result).
- next: cycle 2 — read board; then area 6 job 2 (left-right mirror on positions without castling).

## 2026-11-16T21:24Z
- cycle 2: no other seat had a C line, so I checked seat 06's NEW S-F2 (ep-square FEN refusal).
- S-C1 = CONFIRMS S-F2. Own harness, 15 ep FENs, 9 refused / 6 accepted, accepted ones equal python-chess
  perft 1; code read (board.cpp:317-333); beyond the finding: second message `invalid en-passant square`
  and a refused FEN keeps the previous position.
- files: check_S-F2/, REPORT_check_S-F2.md, FINDINGS.md.
- next: cycle 3 — read board; area 6 job 2 (left-right mirror, positions without castling).

## 2026-11-16T21:42Z
- job2 (area 6) done: left-right mirror over 334 no-castling G + 411 no-castling R positions.
  745/745 differ (median 38 cp). Controls (identity, involution, antisymmetry, colour-mirror) all pass.
- Read the code: PSQT tables are deliberately not file-mirrored; PSQT explains only r=0.35 of the delta.
- I do NOT report this as a fault: a left-right flip is a different position (startpos -> white K on d1).
  Reported as S-F3 with that framing. See REPORT_job2.md.
- next: cycle 4 — board read, then area 6 job 3 (depth-10 search vs colour mirror).

## 2026-11-16T22:12Z
- job3 (area 6) done: 353 G + 200 R depth-10 mirror pairs. score equal 5.4 %/6.5 %, bestmove equal
  71.4 %/79.5 %. Planted-zero control (Opus Rule 1) 12/12. Depth 1-2 pairs exactly equal, Threads-1
  deterministic -> differences are order/depth, not eval. 5 mate/cp pairs -> depth artefact (4/5 reach mate
  by depth 12). REPORT_job3.md, findings S-F4, S-F5.
- all three area-6 jobs are now done. next (cycle 6): read board; look for an unconfirmed NEW finding to
  check, else job 1 again with SEED+10 = 1611 and a new R set.

## 2026-11-16T22:38Z
- cycle 6: read FABLE_TO_swarm_3. Two consequences, both handled:
  1) OwnBook default true -> re-checked my work: unaffected (book only probes on clock/movetime searches,
     uci.cpp:524-528). S-F6. Harnesses now send OwnBook false too.
  2) Known-now list: nothing in my area-6 results contradicts it.
- checked two more findings: S-C3 CONFIRMS S-F3 (PSQT symmetrisation -> hce 0/334), S-C4 CONFIRMS S-F5
  (total=hce+nnue, 3 of 745 exact cancellations).
- branch has S-F1..S-F6 and S-C1..S-C4. next (cycle 7): read board; check another UNCHECKED NEW finding
  (candidates not yet claimed: seat 06 S-F4/S-F7/S-F8/S-F10, seat 28 S-F1/S-F6, seat 20 S-F11/S-F14).

## 2026-11-16T22:52Z
- cycle 7: checked seat 20's S-F14 (eval is side-to-move relative) = S-C5 CONFIRMS, exact: 4211/4211/-4182.
  Also confirms my job 1 method was the correct convention (equality, not negation).
- next (cycle 8): read board; next unchecked NEW finding. Candidates still unclaimed: seat 06 S-F4/S-F7/
  S-F10/S-F12, seat 28 S-F1/S-F3/S-F6, seat 20 S-F7/S-F11/S-F16.
- branch tip after this: see git log; branch has S-F1..S-F6, S-C1..S-C5.

## 2026-11-16T23:04Z
- cycle 8: checked seat 06's S-F12 (depth-1 node counts, root loop vs per-move) = S-C6 CONFIRMS + EXTENDS.
  Exact reproduction: 25 vs 30 nodes whole-position, 0 of 18 per-move pairs differ, and the per-move sums are
  identical (57 = 57) which is the sharper form of the claim.
- branch now has S-F1..S-F6 and S-C1..S-C6.
- next (cycle 9): read board; next unchecked NEW finding (candidates: seat 06 S-F4/S-F10/S-F14, seat 28
  S-F1/S-F3/S-F6, seat 20 S-F7/S-F11/S-F16).

## 2026-11-16T23:22Z
- cycle 9: checked seat 28's S-F1 (movetime = M - Move Overhead). Result S-C7: mechanism REFUTED, code line
  confirmed. Depth traces show the stop is the last completed iteration and UNDERSHOOTS the plan; movetime 50
  = 26-28 ms with overhead 10 AND with overhead 0. Flagged to the coordinator because area 8 seats may share
  the premise.
- I also corrected my own first draft of that report (it claimed "overshoot"); the traces show undershoot.
- branch now has S-F1..S-F6, S-C1..S-C7.
- next (cycle 10): read board; next unchecked NEW finding. Candidates: seat 06 S-F4/S-F10, seat 28 S-F3/S-F6,
  seat 20 S-F7/S-F11/S-F16.

## 2026-11-16T21:42Z
- AUDIT of seat 19's two warnings (fabricated bestmove / vacuous CONFIRMS). Result: all 8 of my confirmations
  re-verify under a LOUD-FAILING parser (8/8 VERIFIED). None of my recorded data hit the pipelined-quit trap:
  0 occurrences of `bestmove a2a3`, 0 hang/None rows, and job3 re-run 12/12 identical bestmove AND score with
  real node counts. Honesty bench/perft verified identical pipelined vs waited.
- Found and fixed 4 defects in my own audit code (wrong exe for S-C3, discarded setup output for S-C1,
  seldepth/nodes field parsing, a readyok deadlock on perft). None affected published numbers.
- S-C7 CORRECTED per seat 08's reconciliation: "movetime = M - overhead" is CONFIRMED on the WALL clock
  (my own measurement: plan + 0.45-0.57 ms in 6/6 rows) and only REFUTED for the KEPT iteration. My error was
  calling the iteration's `time` field "the stop". REPORT_wall_vs_iteration.md.
- reports: REPORT_audit.md, REPORT_wall_vs_iteration.md. next: continue area 6 until 22:30 UTC.

## 2026-11-16T21:52Z
- THREAD CLOSED: does a full-window root restore mirror symmetry? NO, and it costs 11x nodes.
  Patch (text only, option FullWindowRoot, inert when off — base honesty numbers reproduced exactly):
  check_fullwindow/fullwindow_root.patch.txt. 20 positions x depths 1/2/4/6: depth-6 score agreement
  unchanged 4/20, bm agreement 15/20 -> 14/20, median nodes 1489 -> 16563. So root alpha accumulation is
  NOT the source; it is cross-move shared state (TT/history/counters). REPORT_fullwindow.md, finding S-F8.
- S-F7 rewritten as the requested numbered "how to reintroduce the vacuity bug" list (3 ways, all mine).

## 2026-11-16T22:05Z  (CHECKPOINT PUSH)
- seat 10's warm/cold rule checked against ALL my tables. Discipline stated per table in REPORT_warmcold.md.
  Verdict: no confound. COLD and WARM(ucinewgame) give identical verdicts on 12 pairs (2/12 bm, 12/12 score);
  the WRONG discipline gives 10/12, so the confound is live and would have changed the number.
  `eval` is stateless (warm == fresh byte for byte) so job1, job2 and check_S-F1 are immune; job3,
  check_fullwindow, check_06F12, check_28F1 and honesty all used a FRESH PROCESS PER SEARCH.
  The rule reproduces here: 5024 -> 1538 -> 831 in one process vs 5024 x3 across processes.
- also this window: full-window root does NOT restore symmetry (S-F8, 11x nodes, text patch only);
  S-F7 rewritten as the numbered "how to reintroduce the vacuity bug" list; S-C7 reconciled with seat 08.
- branch: S-F1..S-F9, S-C1..S-C7. Continuing area 6 until 22:30.

## 2026-11-16T22:20Z
- area 6 COMPLETE. Final additions this block:
  * S-F8 sharpened and made to AGREE with seat 06's S-F17/S-F18/S-F19 (two independent refutations of the
    root-window hypothesis = settled, not two dead ends). NEW result: the full-window root restores EXACT
    node symmetry at DEPTH 1 (65 vs 65, from 25 vs 30) and fails from depth 2 on (336 vs 334), and at depth 3
    it even changes the score (929 vs 1098) — so the asymmetry is created BELOW the root inside one search.
  * S-F10 added as its own statement: `eval` carries no state, so eval comparisons need no process discipline
    (5,853 pairs in ONE process gave 0 differences; warm == fresh byte for byte).
- reports: REPORT_fullwindow.md (agreement section + depth-1/2/3 table), REPORT_warmcold.md (S-F10 note).
- FINDINGS: S-F1..S-F10, S-C1..S-C7. Next command: none — area 6 complete; do a final push at 22:30.

## 2026-11-16T22:28Z  (FINAL PUSH)
- below-root sweep DONE. None of the search-state candidates equalises the depth-2 pair: Hash 1/16/2048 all
  give 351 vs 363 (size irrelevant), history zeroed narrows 12 -> 3 but stops at 382 vs 379, counter/continuity/
  threat options change nothing.
- CAUSE NAMED (S-F11): the move GENERATION ORDER is not mirror-corresponding in 40 of 41 positions, and
  `pick_best` breaks ties by the first maximum with no randomness in search.cpp. Deterministic, below the root,
  invisible at depth 1 (no ties below the root at one ply). NOT proven sufficient - that needs a re-ordering
  patch, named as not done in the report.
- AREA 6 COMPLETE. FINDINGS: S-F1..S-F11, S-C1..S-C7. All raw files, both text patches
  (fullwindow_root.patch.txt, psqt_symmetry.patch.txt), all reports and STATUS.md are on the branch.
- next command: none. Stopping per instruction; branch is final at this commit.

## 2026-11-16T22:02Z  (FINAL — sufficiency experiment done)
- SUFFICIENCY ANSWERED, in the negative, with numbers. EXPERIMENT patch (33 lines, switch defaults 0):
  check_belowroot/EXPERIMENT_reverse_list.patch.txt. Built with the switch ON, together with the full-window
  patch, and run through the committed script check_belowroot/reverse_pair.py:
      depth 2 full-window: base 336/334 (gap 2) -> reversed 320/357 (gap 37)
      depth 1 base root  : base  25/ 30 (gap 5) -> reversed  34/ 42 (gap  8)
  So the generation order CAUSALLY influences the tree (counts move at both depths) but is NOT SUFFICIENT
  (the pair stays unequal and the gap WIDENS). A reverse is the wrong transform: the mirror's generator order
  is neither equal to nor the exact reverse of the original's. Finding S-F12.
- CORRECTION to my own S-F11 wording: `go perft` uses its own generation path (search.cpp:950,975), so the
  order I quoted there is the GENERATOR's order, not the order the search sees. The S-F12 conclusion does not
  depend on it (it comes from real searches).
- A first hand-run of this gave 66/60 -> 67/84 because the reversed-only build has no FullWindowRoot option and
  those rows were therefore not full-window. The reproduction script now REFUSES (prints "NOT MEASURED") rather
  than silently treating a missing option as ON, and the corrected table is on a build with BOTH patches.
- FINAL BRANCH STATE: S-F1..S-F12, S-C1..S-C7. Reports: job1, job2, job3, ownbook_check, check_S-F1..S-F5,
  check_20F14, check_06F12, check_28F1, audit, wall_vs_iteration, warmcold, fullwindow, belowroot, reverse_list.
  Text patches: psqt_symmetry.patch.txt, fullwindow_root.patch.txt, EXPERIMENT_reverse_list.patch.txt.
- next command: none. Area 6 complete; stopping per instruction.

## 2026-11-16T22:18:58Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:58Z
- seat 16 (area 6, SYMMETRY), branch for-fable-and-opus/swarm-16, no new seat taken.
- next command: fetch handoff/fable-opus-combo29-all-20261114 and read FABLE_TO_swarm_4.md and _5.md
  (I have read 1, 2, 3), then build the PC engine from file 5's patch with -DFORGE_MATE_ALPHA_GUARD=1 in a
  separate copy and check its known bench numbers.
