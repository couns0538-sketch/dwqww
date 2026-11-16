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
