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
