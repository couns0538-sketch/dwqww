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

## 2026-11-16T22:24Z
- PC ENGINE BUILT AND VERIFIED (FABLE_TO_swarm_5): patch sha256 d6bd72c531f785f4 matches; 11 files apply clean
  with `patch -p1` on a pristine 6b98f217 export; built with -DFORGE_MATE_ALPHA_GUARD=1.
  ALL SIX known numbers match: none 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276.
  All 20 option names present in the uci list. Files: pcbuild/PC_BUILD.txt, pcbuild/pc_honesty.sh, pcbuild/raw/.
- THREAD RULE (seat 04): audited every harness. All sweeps that produce scores are Threads 1 — job3,
  check_fullwindow, check_warmcold, check_28F1, check_06F12 and ownbook_check set it explicitly; the four newer
  ones (cold_depth1, below_root_test, order_test, reverse_pair) relied on the DEFAULT, which is verified to be
  Threads 1 both from the uci line and behaviourally (omitting the option gives identical nodes, 66 = 66).
  They now set it explicitly. My 353-pair job-3 sweep WAS Threads 1 (search_mirror.py sends the option).
- next: re-run my own finds on the PC build under PC20 (symmetry of all four new options), Threads 1.

## 2026-11-16T22:34Z
- S-F13: PC r15 + PC20, Threads 1, 20 G mirror pairs at depths 1 and 2. THE ASYMMETRY SURVIVES (depth 2:
  2/20 node-equal, 14/20 score-equal). Of the four new options only TtPruneV2 moves anything (slightly worse);
  the other three are inert at depth <=2 but verified active at depths 6-8. REPORT_pcsym.md.
- next: extend the PC20 symmetry sweep to depth 10 (the 353-pair level) and re-run my base-tree finds on the
  PC build under PC20 as file 5 asks.

## 2026-11-16T22:42Z
- S-F14: full 353-pair depth-10 sweep on the PC build under PC20, Threads 1. Asymmetry WORSE than base:
  120/353 bestmove mismatch (base 101), 0/353 node-equal (not one pair), score-equal 22 (base 19).
  109/353 positions disagree about whether the pair matches -> different asymmetric paths, not the same ones.
  Threads-1 reproducibility 30/30 exact. REPORT_pcsym10.md.
- next: split PC-code effects from PC20-settings effects (base tree under PC20, PC build under S14 only).

## 2026-11-16T22:44Z
- file 6 read. Both "not a defect" verdicts noted (claimable-draw, >Threads-1). New priority understood:
  PC build + PC20 + Threads 1 + softnodes/nodes/6s-clock on real-game positions counts most.
- S-F15: SPLIT result — the extra asymmetry on the PC build is from the PC20 SETTINGS, not the code
  (code alone 101 -> 102 of 353; TtPruneV2 alone 102 -> 113; PC20 120). REPORT_pcsplit.md.
- S-F16: `go softnodes N` on the PC's self-play path is DETERMINISTIC (20 runs, 1 result) and stops at a
  FINISHED depth, but OVERSHOOTS up to 2.06x the budget (2314-4121 nodes at N=2000). REPORT_softnodes.md.
- next: stress the overshoot bound on quiet positions; then the clock path (6s + 0.06), which is the PC's
  match path and is untested by me.

## 2026-11-16T22:53Z
- S-F17: softnodes overshoot bounded ~2.06x RELATIVELY (12 positions at N=2000, none above 2.061x) but NOT
  absolutely: at N=200000 one quiet position overshoots to 1.767x = 353,498 nodes. My P1 (that a quiet position
  would exceed 2.06x) was REFUTED. Determinism and finished-depth held on all 16 runs.
- S-F18: the PC's MATCH path (6s+0.06, PC20, Threads 1) is reproducible in the MOVE (1 distinct bestmove over
  20 runs x 4 positions, bestmove inside its own PV 80/80) but uses only 156-325 ms of the 6060 ms allowed
  (2.6%-5.3%), stopping at depth 17-19; the score has two values per position because the depth reached varies.
  0 of 80 runs over the clock.
- next: does the used-clock fraction change with the clock size (1s / 60s)? That separates "time manager soft
  limit" from "the search really is depth-bounded on this machine".

## 2026-11-16T22:56Z
- S-F19: the clock-usage fraction is a TIME-MANAGER soft limit, not a hardware ceiling — 1s -> 28ms (2.77%),
  3s -> 72ms (2.38%), 6s -> 159ms (2.62%), 30s -> 1312ms (4.33%). It scales with the clock instead of hitting a
  ceiling, so at the PC's 6s control the engine stops early by choice. Flagged to the coordinator as possibly
  mattering to the owner's matches; cause is in the time manager (area 8), not read by me.
- next: back to area 6 substance on the PC path — does the generation-order cause (S-F11/S-F12) behave the same
  on the PC build under PC20? I have the reverse-list patch for the base tree; rebuilding it against the PC tree
  is the direct test.

## 2026-11-16T23:01Z
- S-F20: TtPruneV2 NAMED as the lever. With TtPruneV2 on and the other four EXPLICITLY off, the depth-10
  mismatch is 113/353 (all off 102, PC20 120), and the explicit-off run is identical to the default-off run on
  353/353 positions — so nothing rests on defaults. Turning the option off restores the asymmetry to base level.
- S-F21: the generation-order mechanism transfers to the PC build UNCHANGED — the PC build gives the same node
  counts as the base tree on the S-F12 probe (25/30 base, 34/42 reversed; 66/60, 67/84). So S-F12's
  "necessary, not sufficient" holds on the PC build too, and S-F20's lever is a separate layer on top.
- next: the PC path again — `go nodes` at the match budgets (20000/50000/250000) determinism is done; next is
  whether the TtPruneV2 lever also changes the SCORE asymmetry at depth 10, not just the move mismatch.

## 2026-11-16T23:02Z
- S-F22 REFINES S-F20 and I flagged the refinement to the coordinator: TtPruneV2 is a lever for the
  MOVE-MIRRORING COUNT only (102 -> 113 -> 120), NOT for the score disagreement (score-equal 20/19/22, median
  |mirror score gap| 18/19/16 cp). So it is not a strength lever; the ~18 cp gap is untouched by any option I
  tested. REPORT_lever_scope.md.
- next: PC path — does the ~18 cp mirror score gap shrink with depth (file 6 says a multi-thread spread should
  shrink with depth; the colour gap may behave differently)? Depths 6/8/10/12 on the same positions.

## 2026-11-16T23:06Z
- S-F23: the colour-mirror score gap does NOT shrink with depth — median |gap| 14/17/11/20 cp at depths
  6/8/10/12 (60 positions, PC20, Threads 1), CIs overlapping (approx SE 6-12 cp so indistinguishable), score-equal
  1-9 of 60, move mismatch 24 -> 19. P1 (that it would shrink) REFUTED. So it is a persistent search property,
  distinct from the multi-thread spread file 6 describes which does wash out with depth.
- REPORT_depthgap.md. Running total of findings this block: S-F13..S-F23.
- next: PC path — `go nodes` at 20000 vs 50000: does the MOVE change between them on real-game positions
  (a move changing between two match budgets is the most direct "wrong move at the PC's budget" check).

## 2026-11-16T23:09Z
- S-F24: the PC's own match budgets (`go nodes` 20k/50k/250k, 40 real-game positions, PC20, Threads 1):
  0 illegal moves in 120 searches, move identical at all three budgets on 31/40, and the 8 that change are
  ordinary depth effects — largest +125 cp from the 20k budget to the 250k one (idx 12), one -70 cp
  self-assessment drop in a lost position (idx 37). No blunder found at any real budget. REPORT_nodebudget.md.
- Running total this block: S-F13..S-F24 (12 findings), all on the PC build with Threads 1 except the base-tree
  comparisons I reused.
- next: the one genuinely open question left in my area — does the PSQT symmetrisation (which took hce
  differences to 0/334 on the BASE tree in S-C3) also remove the colour gap on the PC build? That needs the
  symmetrised table applied to the PC tree.

## 2026-11-16T23:14Z
- S-F25 CLOSES the area-6 line: symmetrising the PSQT table does NOT remove the colour score gap (11 cp median
  shipped vs 19 cp symmetrised, 60 positions, PC20, Threads 1) even though the SAME change fixes the left-right
  hce asymmetry completely (S-C3: 328/334 -> 0/334). So the two asymmetries are different phenomena:
  left-right = the PSQT table (fixed); colour-mirror scores = the SEARCH (order dependence, does not shrink with
  depth per S-F23, and the full-window root makes it worse per S-F8).
- AREA 6 on the PC build is now covered end to end: asymmetry survives PC20 (S-F13), full 353-pair count
  (S-F14), code-vs-settings attribution (S-F15), TtPruneV2 named as the move-mirroring lever (S-F20) and its
  scope bounded (S-F22), mechanism transfers from the base tree (S-F21), the gap is depth-persistent (S-F23),
  and the evaluation is ruled out as its cause (S-F25).
- PC path also covered: softnodes determinism + overshoot (S-F16, S-F17), the 6s clock path reproducibility and
  its 2.4-4.3 % clock usage across a 30x range (S-F18, S-F19), and the match node budgets with 0 illegal moves
  in 120 searches (S-F24).
- next: keep testing the PC path — the clock path across a sequence of moves in one process (does the
  increment accumulate, does the engine's own clock bookkeeping drift).

## 2026-11-16T23:24Z
- S-F29: self-play duplication is FIXED by varying the start — ten games from ten DIFFERENT real-game positions
  gave 10/10 distinct final positions and 10/10 distinct move sequences (vs 3/10 from one fixed start, S-F27).
  So the advice to the owner is simply "vary the openings"; the earlier convergence was the fixed start, not a
  deeper search property. Also corrects S-F26's band: across both studies the clock fraction spans 0.02 %-32.24 %
  with a median around 4 %.
- HOUSEKEEPING (self-caught): my S-F16..S-F29 rows had been appended to STRAY paths (forge-combo29/swarm/FINDINGS.md,
  forge-combo29/FINDINGS.md, .../16/softnodes/FINDINGS.md) because of a wrong relative path in my shell commands.
  All rows are now consolidated into forge-combo29/swarm/16/FINDINGS.md (34 rows: S-F3..S-F29 plus S-C1..S-C7) and
  the strays are deleted. VERIFIED: nothing outside my own folder was ever committed — `git log --diff-filter=A`
  since my seat commit shows no additions outside forge-combo29/swarm/16/.
- FINAL.md updated with S-F29 and the corrected clock band.

## 2026-11-16T23:26Z
- FINAL.md PART 4 now opens with a line stating that EIGHT self-corrections follow (two refutations of my own
  published numbers, two bugs in my own audit harness), so a reader sees the failures before the successes.
- WARNING_stray_paths.md added: the wrong-relative-path trap that silently scattered 20 of my findings across four
  files, with the two validation commands that catch it (table well-formedness; `git log --diff-filter=A` proving
  nothing outside my folder was ever staged). Written so another seat can copy the checks verbatim. I cannot write
  to another seat's branch, so it lives in my folder for relay.
- next: hold the cadence to the close at 10:19Z; the FINAL block goes in at that time.

## 2026-11-16T23:28Z
- The two integrity checks are now ONE RUNNABLE SCRIPT, not paste-only: forge-combo29/swarm/16/check_folder.py.
  It checks (1) every `| S-` row splits into 4 fields (C-row) or 5 (F-row) — which catches a pipe inside a cell
  AND reports the id gaps a stray row leaves — (2) `git log --diff-filter=A` from the seat commit shows nothing
  outside the folder, (3) no binary/non-UTF-8 file. Exit 0 = clean.
- VALIDATED AGAINST PLANTED FAULTS, because a green result from an unchecked script is worth nothing: in a
  scratch repo I planted both failures I had suffered (a `median |gap|` row and a FINDINGS.md outside the seat
  folder) and the script reported BOTH with exact fields and path; on my real folder it reports 34 rows / 34 ids /
  malformed none / OUTSIDE none / non-text 0 / ALL CHECKS PASS.
- FINAL.md now has PART 4b carrying this as the transferable result, with a link to WARNING_stray_paths.md.

## 2026-11-16T23:30Z
- check_folder.py is now documented as a SWARM-WIDE TOOL rather than a seat artefact: its header carries the
  usage line (`python3 check_folder.py NN [REPO]`), what each of the three checks catches and why, a
  pre-FINAL gate snippet, an explicit "what it does NOT check" (record integrity, not truth of a finding),
  the planted-fault provenance, and a note that `FINDINGS.md: MISSING` for ANOTHER seat's number is expected
  because each checkout holds only its own folder.
- Re-verified after the header rewrite both ways: passes on my folder, still fails on the planted faults
  (malformed row + stray path), and zero-pads `7` -> `07` correctly.
- Folder now holds two reusable tools (check_folder.py, and the two text patches) and two hazard notes
  (WARNING_stray_paths.md, plus the audit report). Holding cadence; FINAL block at 10:19Z.

## 2026-11-16T23:36Z
- S-F30: the PC's 2,000-node self-play budget vs its 250,000-node match budget, 40 real-game positions:
  25/40 SAME move, median cost 0 cp, 4 worse by >30 cp (worst +109, idx 34) and 3 BETTER by >30 cp (best -109).
  So "self-play at 2,000 nodes plays badly" is NOT supported — useful negative for the owner.
- FIFTH SELF-CORRECTION (my own): the first summary had the cost SIGN INVERTED, so a rook-winning move (h8h1,
  idx 37) scored as the worst blunder of the run. Caught because I already knew that move wins a rook from S-F24;
  verified at depth 14 (mover's score -568 after h8h1 vs -613 after h8g8) and corrected throughout. FINAL PART 4
  now reads "nine self-corrections" and lists this one with the lesson: a result that contradicts something you
  already know is the cheapest available bug detector.
- check_folder.py: ALL CHECKS PASS on the folder (374 files, 0 non-text, 35 findings rows).
- Holding cadence; FINAL block at 10:19Z.

## 2026-11-16T23:38Z
- FINAL.md updated per the coordinator's two points:
  1. The rule is now in verbatim as its own quoted block inside self-correction 8: "A result that contradicts
     something you already know is the cheapest available bug detector — and it only works if you keep your
     earlier findings in view." with the note that the contradiction was visible in one glance because S-F24 was
     already on the branch.
  2. The softnodes-vs-nodes wash is now its own prominent block, 2.3a, headed "THE SELF-PLAY BUDGET DOES NOT
     PLAY BADLY — a removed worry, not a found fault", with the four numbers, the framing that it removes a
     concern rather than adding one, and its relation to S-F29 and S-F16 (so the self-play path is summarised
     in one place: ~1.7x node overshoot and the need for varied starts are the two things to know, not move
     quality).
- check_folder.py: ALL CHECKS PASS. Holding cadence to the close.

## 2026-11-16T23:48Z
- S-F31 CORRECTS my own S-F30 and changes the answer to the coordinator's "removed worry". I re-judged all seven
  of S-F30's |cost|>30 cases with deeper reference searches (depths 12/14/16/18):
    * every SIGN survived (7 of 7) — so S-F30's individual cases are real, not depth-12 proxy artefacts;
    * but the MAGNITUDES of the four LOSSES GREW (+92->+130, +79->+69, +39->+209, +109->+136) while the three
      GAINS stayed modest (-58, mate, -63).
  So "the self-play budget is a wash" is true in COUNT (4 worse vs 3 better) but NOT in magnitude. The accurate
  statement, now in FINAL 2.3a: the 2,000-node budget errs about as often in each direction, but its errors cost
  more than its lucky wins — and if the owner is choosing a self-play budget for strength, the evidence says move
  up from 2,000. My P2 (that the magnitude would shrink with depth) was REFUTED.
- I also caught and fixed a nonsense word ("magistrates" for "magnitudes") in that same FINAL edit within a
  minute of writing it; worth recording because a garbled word in a summary is exactly what makes a careful
  reader distrust the numbers beside it.
- check_folder.py: ALL CHECKS PASS (380 files, 36 findings rows). Holding cadence; FINAL block at 10:19Z.

## 2026-11-16T23:52Z
- FINAL 2.3a restated so the corrected line cannot be misread. The old heading said "a removed worry, not a found
  fault", which S-F31 CONTRADICTS, so it is gone (0 occurrences of "removed worry" left in the file). The block
  now:
    * heads with the verdict itself: the budget errs about as often in each direction, but its errors cost more
      than its lucky wins, so a strength-minded choice should move up from 2,000;
    * repeats it as a quoted verdict box directly under the numbers, with the explicit note that the count is
      genuinely even at 4 against 3 and that a count is the wrong measure for a strength decision;
    * then derives it from the depth 12/14/16/18 re-judgement.
  The redundancy is deliberate: the opening sentence serves a skimming reader and the derivation serves a
  sceptical one, and this is the one line in my folder that must not be misread.
- check_folder.py: ALL CHECKS PASS. Holding cadence; FINAL block at 10:19Z.

## 2026-11-17T00:06Z
- S-F32 answers the follow-up my own S-F31 created: I told the owner to move up from 2,000 nodes but not TO WHAT.
  Measured four budgets against a 250,000-node reference on 39 real-game positions, each move judged by a fixed
  depth-16 search:
      budget | same move as ref | median cost | >30 worse | >100 worse | TOTAL DAMAGE
        2000 |  21 of 39 | +0 cp | 3 | 0 | +213 cp
        8000 |  28 of 39 | +0 cp | 2 | 0 | +180 cp
       20000 |  31 of 39 | +0 cp | 1 | 0 |  +96 cp
       50000 |  34 of 39 | +0 cp | 1 | 0 |  +69 cp
  Monotone improvement, no reversal; the knee is 20,000 (2.5x more nodes beyond it buys only 27 cp).
  RECOMMENDATION now concrete and in FINAL 2.3a: move self-play from 2,000 to 20,000 nodes.
- The methodological point S-F31 started is now clean: the MEDIAN cost is 0 cp at every budget, which is why
  median was the wrong statistic in S-F30 and the SUM of positive costs is the right one for a budget used over
  many moves.
- check_folder.py: ALL CHECKS PASS (387 files, 37 findings rows). Holding cadence to the close at 10:19Z.

## 2026-11-17T00:12Z
- FINAL 2.3a: the relative-to-250k caveat moved from the report INTO the verdict box, beside the number it
  qualifies, as the coordinator asked. It now also states a cost I had been leaving out of the recommendation:
  raising the budget to 20,000 is 10x the nodes of 2,000, which I did not quantify, and for a training loop
  throughput may matter as much as the 117 cp of accumulated damage it saves. A recommendation that quotes only
  its benefit is not a complete recommendation.
- check_folder.py: ALL CHECKS PASS. Holding cadence to the close at 10:19Z.

## 2026-11-17T00:34Z
- ANOTHER SEAT'S CORRECTION CHECKED, and it is right on its own terms: on all 353 G positions under PC20 at
  Threads 1,
      depth 1: scores equal 353/353, bestmoves 352/353, but NODE COUNTS only 112/353 (68% already unequal)
      depth 2: scores 242/353 (111 unequal = 31.4%), bestmoves 321/353, node counts 41/353
  So "the asymmetry begins at depth 2" is CORRECT for scores and bestmoves (their 27% on 30 positions sits inside
  my 31.4% on 353) and WRONG for node counts, which show it from the first ply. S-F33.
- ELEVENTH SELF-CORRECTION, found by re-examining my own wording: S-F8 said the full-window root "restores exact
  node symmetry at DEPTH 1 ONLY (65 vs 65)". That was ONE POSITION stated as if general. Across 20 positions the
  same change improves depth-1 node equality only 9/20 -> 11/20, NOT to 20/20. The experiment and its depth-2/3
  results stand; the generalisation does not. FINAL 1.3 now carries the caveat and a per-quantity onset table, and
  PART 4 lists this as correction 9 of ten.
- Also priced the S-F32 recommendation (throughput_cost): 20,000 nodes is 5.8x the wall time of 2,000 on this box
  (12.8 ms vs 2.2 ms per move), so the 117 cp saving costs ~5.8x fewer self-play games per hour. That closes the
  gap I had flagged in the verdict box.
- check_folder.py: ALL CHECKS PASS (398 files, 38 findings rows). Holding cadence to the close at 10:19Z.

## 2026-11-17T00:42Z
- FINAL now opens with a STANDING CAUTION (before PART 1, so no reader can miss it) stating the single species my
  eleven self-corrections belong to — a single case written in language that sounds like a property — with the
  four clearest instances named and SIX HABITS listed that produced them:
    1 a count is not a magnitude; 2 a median hides a tail; 3 a single probe is not a property;
    4 a correlation needs the right model; 5 a sign is not obvious; 6 a parser that cannot fail cannot confirm.
  It closes by naming which results ARE strong (the ones where a large N and an independent check agree): the
  353-position counts, the 25,532-pair eval symmetry, the 600-move clock study, and the 8-of-8 re-verification of
  my confirmations. PART 4 cross-links to it so the instances read as one pattern rather than eleven slips.
- That is the structural fix the coordinator asked for: a reader can now discount for the author's characteristic
  error before reading any number, instead of discovering it in a list at the end.
- check_folder.py: ALL CHECKS PASS (398 files, 38 findings rows). Holding cadence to the close at 10:19Z.

## 2026-11-17T00:50Z
- Restructured the STANDING CAUTION so the SIX CHECKS LEAD and are worded so they apply to anyone's work (not just
  mine): a count is not a magnitude; a median hides a tail; a single probe is not a property; a correlation needs
  the right model; a sign is not obvious; a parser that cannot fail cannot confirm. Each now ends with the
  generalisable instruction (the last one: "any check you rely on should be shown to FAIL on a planted fault
  before you trust it to pass on a real one"). The instances follow as the shape to recognise, then the strong
  results that survive the checks.
- CAUGHT MY OWN ARITHMETIC while doing it: I had been writing "eleven self-corrections" for hours, but PART 4
  contains TEN numbered entries — because entry 10 bundles three separate harness bugs (wrong build passed,
  setup output discarded, seldepth parsed as nodes). So the honest statement is "ten entries covering twelve
  distinct errors", and FINAL now says exactly that in both places, with the breakdown by kind (2 refutations of
  my own numbers, 4 harness/audit bugs, 2 wrong pre-registered predictions, 1 inverted sign, 1 single-case-as-
  property). A count I repeated without rechecking is the same failure the caution warns about.
- check_folder.py: ALL CHECKS PASS (398 files, 38 findings rows). Continuing to the close at 10:19Z.

## 2026-11-17T01:05Z
- Built check_claims.py: an attempt to MECHANISE the six habits so another seat can run them rather than read them.
  Tested it against a deliberately well-formed report and a deliberately bad one: silent on the first, all six
  habits firing on the second. So it discriminates, at least on clear cases.
- BUT I MEASURED ITS LIMITS ON MY OWN WORK AND RECORDED THEM IN ITS HEADER rather than shipping it as a gate: over
  my 36 reports it produced 216 candidate lines and on inspection the large majority were FALSE POSITIVES. Habit 3
  fired 29 times mostly on the word "identical" in prose that DOES report its sample size; habit 5 fired 23 times
  on the word "cost" in sentences making no comparison. Prose ABOUT rigour reads exactly like prose LACKING it.
  What mechanises reliably: habit 2 (median with no tail in the report), habit 1 (bare "N worse, M better"), habit 6
  (zero-result claim with no planted case). What does NOT: habits 3, 4, 5 — those need a reader's question.
- AND IT FOUND THREE REAL GAPS IN MY OWN REPORTS, which I fixed: REPORT_job3.md, REPORT_fullwindow.md and
  REPORT_wall_vs_iteration.md all quoted MEDIANS with no tail statistic. job3 now carries median/p90/max per set
  (G: 18/60/541 cp; R: 28/83/236 cp — so the worst mirror gap is 30x the median, which the median alone hid).
  fullwindow now records that its 11.1x cost ratio is a ratio of MEDIANS. wall_vs_iteration: I checked the raw
  file and the individual run times were never saved, so I recorded that as a GAP I cannot close rather than
  estimating a number, with the command to re-run if it matters. Habit 2 is now clean on all 36 reports.
- check_folder.py: ALL CHECKS PASS. Continuing to the close at 10:19Z.

## 2026-11-17T01:10Z  (end time corrected: 10:18:40Z, ~9h remaining)
- FINAL now states the window ends 2026-11-17T10:18:40Z (was 10:19Z), and the 30x ratio is promoted into the
  STANDING CAUTION itself as habit 2's own example: the colour-mirror score gap has a MEDIAN of 18 cp and a MAX of
  541 cp — a factor of 30 between typical and worst — and every summary I wrote from the median alone understated
  the asymmetry by that factor. The caution now also records that I wrote that rule and then found it broken in
  three of my own reports within the hour.
- Cadence continues for the remaining window (not "to a close"): STATUS every 25 minutes or less, findings and
  checks as they land, FINAL block at 10:18:40Z.
- next: the one experiment I left open from S-F21/S-F12 — whether a MIRROR-ORDER permutation (not a reverse) makes
  the pair equal. That is the correct transform and it is the last untested step of the symmetry thread.

## 2026-11-17T01:36Z
- S-F34: THE LAST UNTESTED STEP OF THE SYMMETRY THREAD, DONE, and the answer is "major factor, not the whole cause".
  I forced a canonical MIRROR-INVARIANT move order (sort each generated list by colour-relative from/to squares),
  which is the transform S-F12 said was correct instead of a reverse:
      probe pair:  depth 1  25/30 -> 37/37 EXACTLY EQUAL,  depth 2  66/60 -> 79/79 EXACTLY EQUAL (scores match too)
      5 positions x 3 depths: 10 of 15 exactly equal  (the reverse in S-F12 made things WORSE)
  So generation order is a major cause and my S-F12 mechanism was misidentified (the reverse was the wrong
  transform). NOT sufficient: 5 of 15 still differ, and that residue is INDEPENDENT of hash size (identical at
  Hash 1/16/256 MB), so it is not the transposition table.
- CAUGHT A HARNESS ERROR while doing it: my first p3 test used a hand-typed mirror FEN that was WRONG in three rows
  (I had the mirror in check with 2 legal moves vs the original's 25). The multi-position run computed mirrors with
  chess.Board(f).mirror() so its numbers stand; I re-ran p3 with the correct mirror and the residue is the same.
  From now on every mirror FEN in my harnesses is computed, never typed.
- I deliberately tested beyond the probe position BEFORE writing it up: the probe alone would have made this look
  like a complete explanation, which is exactly the trap my STANDING CAUTION habit 3 warns about.
- files: mirror_order/ (REPORT, EXPERIMENT_mirror_order.patch.txt, search.cpp.experiment.txt, raw_*.txt).
- Cadence continues for the remaining window; next FINAL block at 10:18:40Z.

## 2026-11-17T02:05Z
- S-F35: THE SYMMETRY THREAD IS CLOSED WITH A COMPLETE MECHANISM. Canonicalising EVERY move-generation site by a
  mirror-invariant key makes the colour-mirror pair EXACTLY equal in 15 of 15 position x depth cases.
    base PC r15                     0 of 15
    + captures & quiets            10 of 15   (probe pair already exactly equal)
    + root candidate list          10 of 15   (root was NOT the residue)
    + EVASION generator            15 of 15   <- THE ANSWER
  The decisive site is the evasion generator (search.cpp:1078), which fires only inside subtrees and so never
  showed at the root. I ruled out, by measurement, before finding it: the transposition table (identical mismatch
  at Hash 1/16/256), history/counter state (unchanged across 7 configurations), and root order.
- Correct framing in the report: this is a DIAGNOSTIC, not a speed or strength proposal. The canonical order
  discards the tuned ordering that gives the engine its strength, which is why node counts rise. The owner's
  engine should NOT adopt it; its asymmetry is the cost of its ordering, now fully understood.
- S-F34 is marked SUPERSEDED by S-F35 in FINDINGS (my 10-of-15 was correct for the two sites then canonicalised).
- Deliverables: mirror_order/REPORT_mirror_order.md, EXPERIMENT_mirror_order.patch.txt (80 lines, patch -p2 clean,
  switch defaults 0), search.cpp.experiment.txt, raw_mirror_order/raw_multi/raw_multi2/raw_multi3/raw_hash1/raw_residue.
- check_folder.py ALL CHECKS PASS (411 files, 42 findings rows). Cadence continues; FINAL block at 10:18:40Z.

## 2026-11-17T02:32Z
- Restructured REPORT_mirror_order.md per the coordinator's two points:
  1. The DIAGNOSTIC-NOT-A-PROPOSAL box is now the FIRST thing after the title, with the reason stated (the
     canonical order discards the tuned ordering — TT move first, then score/SEE/history — which is where the
     engine's strength comes from, hence node counts rising 60 -> 79). It also names what a real fix would need:
     an ordering that is BOTH score-based and mirror-invariant (score every move, then break ties by the canonical
     key), which is a different piece of work and is explicitly not attempted.
  2. The THREE NEGATIVE RESULTS now sit together in their own section, as a table, ahead of the positive result:
     transposition table (identical at Hash 1/16/256), history/counter state (unchanged across seven
     configurations), root move order (still 10 of 15 when the root list was canonicalised). The section ends with
     the reasoning they enabled: a difference surviving every state-table and root-level change, but varying by
     position, points at a code path reached only in some nodes — which is what the evasion generator is.
- The same framing and the same three negatives are now in FINAL 1.4, since that is what Opus reads.
- check_folder.py ALL CHECKS PASS (411 files, 42 findings rows). Cadence continues; FINAL block at 10:18:40Z.

## 2026-11-17T03:05Z
- S-F36: I ATTEMPTED the "stated next step" rather than leaving it as a note, and it FAILS — which is worth more
  than the note. The cheap fix (keep the score-based ordering, break only TIES by a mirror-invariant key) reaches
     base PC r15                          3 of 15
    score order + canonical tie-break     7 of 15
    full canonicalisation (S-F35)        15 of 15
  The reason is structural, and it corrects my own formulation: a tie-break acts only when two moves score EXACTLY
  equal, but the asymmetry also arises among UNEQUAL scores through order-dependent pruning (LMR, futility, SEE
  thresholds), which a tie rule never touches. So the collision between symmetry and strength is at the PRUNING
  DECISIONS, not at the tie-break, and no cheap formulation exists that I could find.
- I therefore CORRECTED the "both score-based and mirror-invariant" sentence in FINAL 1.4 and in
  REPORT_mirror_order.md: it no longer reads as a promising next step, it reads as attempted-and-failed with the
  mechanism. S-F35's diagnostic is the deliverable; a strength-preserving fix is not something I can produce.
- Deliverables: tiebreak/REPORT_tiebreak.md, EXPERIMENT_tiebreak.patch.txt (48 lines, patch -p2, switch defaults 0,
  and with the switch on the AVX2 lane shortcut is compiled out so the scalar tie rule governs), raw_tiebreak.txt.
- check_folder.py ALL CHECKS PASS (417 files, 43 findings rows). Cadence continues; FINAL block at 10:18:40Z.

## 2026-11-17T03:20Z
- Per the coordinator: the MECHANISM sentence now leads REPORT_tiebreak.md, as a quoted block directly under the
  title: "order-dependent pruning — LMR, futility and SEE thresholds — consumes move order and decides which moves
  are ever compared, long before any tie is reached, so a rule that only breaks TIES never touches the decisions
  that actually create the asymmetry." The same sentence is in FINAL 1.4.
- THEN I VERIFIED THE MECHANISM IN THE SOURCE rather than leaving it as an assertion, and added the four line
  references to the report: LMR is `reduction(quiet, depth, move_count)` (search.cpp:1994, a function of list
  POSITION); LMR exempts the first move via `move_count > 1 + ...` (1992, so order decides who is exempt);
  late-parent relief depends on `arrival_index` and `move_count` (2010); and the SEE pruning threshold is applied
  per move as picked (618). None of the four is a tie comparison — each fires on a move whose score DIFFERS from
  the best so far, which is exactly why a mirror-invariant tie rule cannot reach them.
- That closes the symmetry thread with mechanism, code citations, a diagnostic, and an explicit statement that no
  cheap strength-preserving fix exists. Nothing further owed on it; continuing the cadence on the PC path.
- check_folder.py ALL CHECKS PASS (417 files, 43 findings rows). FINAL block at 10:18:40Z.

## 2026-11-17T03:52Z
- S-F37: I TESTED MY OWN "COMPLETELY" against my own habit 3. S-F35's claim rested on 15 cases; habit 3 says a
  small sample is not a property, and "completely" is exactly the word that needs a larger N.
    depth 1: base equal 25/60  ->  canonical 60/60
    depth 2: base equal  9/60  ->  canonical 60/60
    ALL    : base equal 34/120 ->  canonical 120/120
  ZERO residue. ZERO cases the fix broke. So S-F35 generalises on 120 cases and the sample-size caveat I would
  otherwise have owed is withdrawn; FINAL now states 120 of 120 against the base build's 34 of 120.
- P4 of that job was REFUTED (I predicted depth 1 would be equal more often than depth 2 IF a residue existed;
  there is no residue, so the premise never arose) and I recorded the refutation rather than dropping it.
- Framing unchanged: still a DIAGNOSTIC, still not something the owner should adopt (S-F36's cheap variant failed
  with a source-verified reason).
- check_folder.py ALL CHECKS PASS (424 files, 44 findings rows). Cadence continues; FINAL block at 10:18:40Z.

## 2026-11-17T04:20Z
- THE STRAY-PATH BUG RECURRED, and this time my own tool missed it — worth reporting plainly.
  My S-F30..S-F37 appends (11 rows) went into forge-combo29/swarm/FINDINGS.md again, because I kept using relative
  paths. My check_folder.py did NOT catch it, and the reason is a real blind spot: it scanned
  `git log --diff-filter=A`, which only sees COMMITTED files, and the stray was never `git add`ed. It reported
  ALL CHECKS PASS while 11 of my 45 rows were in the wrong file. I found it only by grepping for S-F37 after the
  coordinator asked me to name the sample in the claim.
- FIXED BOTH: (a) the 11 rows are consolidated into my own FINDINGS.md and the stray is deleted; (b) check_folder.py
  now ALSO runs `git status --porcelain --untracked-files=all` and reports anything changed or untracked outside
  the folder — because an uncommitted stray is still a stray, and it is the most likely state when you run the
  check. The header says scan (b) was added after a real miss.
- Also fixed while consolidating: 4 rows had wrong column counts (my correction notes were 4-column, and S-F31 had
  a pipe inside `|cost|`), and the checker now recognises same-id CORRECTED/QUALIFIED/SUPERSEDED notes as
  legitimate rather than as duplicates.
- Standing lesson recorded: running a check is not the same as running a check that can see the failure. My tool
  passed because its scan looked at the wrong layer (committed, not working tree) — the same species as seat 19's
  vacuity trap, one level up.
- check_folder.py ALL CHECKS PASS (424 files, 45 findings rows, both stray scans clean). Cadence continues.

## 2026-11-17T04:35Z
- The sentence the coordinator asked me to keep is now in FINAL's STANDING CAUTION as the sharper form of habit 6:
  "running a check is not the same as running a check that can observe the fault", with the instance (my
  folder-integrity script reporting all-clear while 11 of 45 rows were in the wrong file, because it scanned
  committed files and the stray was uncommitted) and the instruction that follows: before trusting a green result,
  ask which LAYER it looked at.
- I then PROVED the fix rather than asserting it, which is the same standard I applied to the original tool: in a
  scratch repo I planted an UNCOMMITTED stray FINDINGS.md outside the seat folder. Scan 2 (committed) reported
  clean — the old blind spot, reproducing exactly — and scan 2b reported
  `['?? forge-combo29/swarm/FINDINGS.md']` and failed the run. So the check now observes the fault it previously
  missed.
- Both scans are documented in WARNING_stray_paths.md with that planted-fault transcript, and the reason two scans
  are needed (committed-then-deleted vs exists-now-uncommitted, the latter being the likelier state when you run it).
- check_folder.py ALL CHECKS PASS (424 files, 45 findings rows, both scans clean). Cadence continues; FINAL block at
  10:18:40Z.

## 2026-11-17T04:50Z
- Verified both sentences the coordinator asked to keep are in place, rather than assuming:
  1. In FINAL's STANDING CAUTION (habit 6, line 50): "Before trusting a green result, ask which LAYER it looked at."
     — kept as written.
  2. In check_folder.py the two-scan reason is now stated crisply as the coordinator put it: COMMITTED-THEN-DELETED
     and UNTRACKED-NOW are different faults with different lifetimes, (a) sees the first and is blind to never-
     committed, (b) sees the second and is blind to already-deleted, and both are needed because the untracked-now
     state is the likelier one when you run the check (you have just written the row that went astray).
- Re-verified the tool both ways after the header edit: ALL CHECKS PASS on my real folder, and it still FAILS on the
  planted uncommitted stray in the scratch repo. A doc edit to a check deserves the same re-test as a code edit.
- check_folder.py ALL CHECKS PASS (424 files, 45 findings rows). Cadence continues; FINAL block at 10:18:40Z.

## 2026-11-17T05:20Z
- S-F38: SEAT 11'S TEST ANSWERED, and it CORRECTS my S-F27. At a FIXED limit the same start gives ONE distinct move
  sequence in 10 of 10 games — at `go nodes 20000` AND at `go depth 10` (PC20, Threads 1, Hash 16, one process per
  game, 20 plies). Seat 11's independent clock run also gave 1 of 10. So my "3 distinct final positions out of 10"
  was a CLOCK ARTEFACT OF MY OWN HARNESS, not an engine property: my clock arm decremented by measured wall time,
  so millisecond differences occasionally changed the depth reached. My S-F27 note had the mechanism right and then
  reported the count as if it were the engine's. S-F27 is marked CORRECTED; S-F29's "vary the openings" is
  unaffected and strengthened (one fixed start = exactly one game).
- The stray-append bug recurred a THIRD time and was caught by the new untracked-files scan BEFORE it compounded —
  the fix working. One row (S-F38) recovered. ROOT CAUSE now addressed with addf.sh: a tiny appender that resolves
  FINDINGS.md absolutely, refuses input that is not a `| S-` row, and warns when the id already exists. Tested both
  ways (refuses non-rows; appends a real row; restore verified).
- Also built the file-7 v3 toolchain: make_v3_testnet.py reproduces the test net EXACTLY (6,309,096 bytes,
  fnv1a64 fdff70de72e4ca82, sha256 1db8525e...) and the v3 engine builds with NNUEArch present. Step 0 next.
- check_folder.py ALL CHECKS PASS (432 files, 46 findings rows). Cadence continues.

## 2026-11-17T05:55Z
- FILE 7 STEP 0 RUN AND STOPPED, per its own rule. Result: SEVEN of eight bench numbers and ALL THREE eval lines
  match file 7 exactly. The one failure is `net_only bench 13`: 4,151,906 against the published 4,191,906 —
  reproducible over three consecutive runs, so a build difference, not noise.
- The net itself is verified: load line reads checksum fdff70de72e4ca82, max 64/96/16, kernel avx512 — every
  field file 7 requires to match does match. So this is NOT a bad net load.
- My environment differs from the PC's and that is the likely cause: Intel Xeon vs AMD Zen 5, g++ 13.3.0 vs clang,
  -march=x86-64-v4 vs znver5. Supporting evidence: only the net-DOMINATED row moves, while all three rows that
  include PC20 pruning match exactly. I tried to test the compiler half with clang 18 and could not — clang fails
  to link on this machine — so the hypothesis is stated as a hypothesis.
- Because one identity row is already wrong, I did NOT start Steps 1-3: a speed patch must keep those rows, so
  any patch measured here would inherit the disagreement. That is file 7's own instruction, not my choice.
- Two harness bugs found and fixed en route, both worth naming: (a) my wait loop for `bench` expected bestmove
  when bench answers `info string bench ...` + readyok, so the first run hung at 0% CPU; (b) I sent `ucinewgame`
  AFTER `position`, which resets the board to startpos on this tree (seat 12's S-F1), so every eval returned 968.
  Both were caught by the numbers being wrong, not by inspection.
- addf.sh earned its keep twice: it refused to write when invoked from the wrong directory, and it refused a
  `| v3` row until I widened its guard to file 7's tagging convention — a refusal, never a stray.
- check_folder.py ALL CHECKS PASS (440 files, 47 findings rows). Cadence continues to 10:18:40Z.

## 2026-11-17T06:30Z
- STEP 0 IS SETTLED AND IT PASSES: 8 of 8 bench numbers and 3 of 3 eval lines match file 7. My earlier "40,000-node
  hardware discrepancy" was MY OWN TRANSCRIPTION ERROR — file 7 says net_only bench 13 = 4,151,906 and I had typed
  4,191,906 into my harness's expected-value table. Verified byte-for-byte with `od -c` on the published row:
  `4 1 5 1 9 0 6`. My build matched on the very first run.
- THE WORST PART IS THE ORDER OF MY REASONING, and it is worth recording plainly: three other seats (11, 29, 15) on
  the SAME hardware and compiler reported that pair as matching. I had three independent measurements against my one
  reading, and instead of re-reading the digit I constructed a plausible hardware explanation on top of my error and
  offered to hand the job over. A digit is cheaper to check than a hypothesis. That is habit 3 of my own caution
  (a single case dressed as a property) applied to an ERROR rather than a result, and it is the seventh
  self-correction on the branch and the most avoidable. The check that would have caught it: quote the published
  figure byte-for-byte instead of retyping it.
- The job is UN-STOPPED and Step 1 begins: prediction committed alone first, then perf on bench 13 under PC20 + the
  test net and on 200 openings at depth 12.
- check_folder.py ALL CHECKS PASS (441 files, 48 findings rows). Cadence continues to 10:18:40Z.

## 2026-11-17T07:05Z
- STEP 1 DONE, AND ALL FOUR PREDICTIONS WERE WRONG. The v3 net path is 20.85 % of bench-13 time under PC20 + test
  net — my prediction said 55-85 % and my own kill criterion was "under 40 %", which fired. The hottest v3 symbol is
  the INCREMENTAL UPDATE `apply_changes_pair` at 8.24 %, NOT the forward pass (`evaluate` 4.81 %).
- The profile's useful surprise: move generation and the picker total ~37 % (pick_best 8.47, its internal sort 5.03,
  generate_evasions 7.55, next 4.81, fill_pseudo_legal 3.43, is_legal_complete 3.20, see_ge 4.35) — MORE than the
  whole net path. So a perfect v3 kernel caps at ~1.26x on this workload, and the larger lever is the picker. That
  is a ceiling the owner should know before Step 2 patches land.
- Environment notes for other seats: perf was absent and installable; it then refused because perf_event_paranoid
  was 2 (I set it to -1 with sudo), and the version wrapper refuses on kernel 6.12.113+ while the 6.8 perf BINARY
  works fine — call /usr/lib/linux-tools/6.8.0-149-generic/perf directly.
- Housekeeping: my check caught a perf.data binary in the folder before it was committed. Removed, and .gitignore
  now covers *.fnn3, perf.data*, __pycache__/. ALL CHECKS PASS (451 files, 0 non-text, 49 findings rows).
- next: file 7's second profiling arm — 200 openings at depth 12 — before I draw the final conclusion on where the
  time is, since bench 13 is not the PC's workload.

## 2026-11-17T08:00Z
- STEP 1's SECOND ARM DONE AND THE CEILING HOLDS. 40 real positions at depth 12 under PC20 + test net:
  nnue:: 20.65 % against bench-13's 20.85 % — inside 0.2 points, so the ~1.26x ceiling for v3 kernel work is NOT a
  bench artefact. picker+generation 34.17 % (bench ~37 %), confirming the picker as the larger lever in both.
- The second arm DID change the internal ranking, which is exactly why file 7 asked for two: on the bench the
  incremental update `apply_changes_pair` (8.24 %) is hottest, but on real positions `evaluate` (6.18 %) overtakes
  it (5.98 %). So a patch should target the shared accumulator walk, not either symbol alone — that is the actionable
  line for Step 2.
- My P1 and P2 of that pre-registration were REFUTED (I expected the net share to RISE on real positions and
  `apply_changes_pair` to stay hottest); P3 and P4 confirmed. Recorded all four.
- TWO HARNESS FAILURES caught by the data, both worth other seats knowing:
  (1) I hit seat 19's fabricated-bestmove trap — pipelining 40 searches then `quit` gave `bestmove a2a3` eight
      times with ZERO depth-12 lines. Rewrote to drive each search to bestmove; 40/40 rows. I checked whether this
      also invalidated my S-F38 result and it does NOT (that harness reads to bestmove).
  (2) `perf report --stdio` REDIRECTED to a file emitted only 4 kernel symbols while the same command in a terminal
      showed 58 including user symbols. `--sort symbol` fixed it. A redirected perf report can silently
      under-report, which would have produced a completely wrong profile.
- check_folder.py ALL CHECKS PASS (467 files, 0 non-text, 51 findings rows); the perf.data binaries are ignored.
- next: Step 2 — one speed patch to the shared v3 accumulator walk, .patch.txt, keeping every identity row.
