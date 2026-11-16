# STATUS — Seat 11

## 2026-11-16T21:07:00Z (times from `date -u` in stamps.txt)
seat 11
area 1 — FEN INPUT under ASan + UBSan
branch for-fable-and-opus/swarm-11
seed 1101

- [x] STEP 1 seat claimed (SEAT.txt committed, token echoed back from origin)
- [ ] STEP 2 build 6b98f217 + honesty check
- [ ] THE CYCLE

Next command: `cd /agent/repos/dwqww && git worktree add ../base 6b98f2170a3210e71beed04bbd2553972c253ed7`

- [x] STEP 2 honesty check: 312866 / 862329 / 3024920 / 4865609 ALL MATCH (HONESTY.txt)
- [x] ASan+UBSan build started

## 2026-11-16 (cycle 1)
- job1 DONE: 20k mutated FENs under ASan+UBSan, 0 crashes / 0 san lines (both proofs shown).
- Read Opus FABLE_TO_swarm_1.md: F1 is new; F2 already known (kept only the harmlessness proof);
  S-F3 WITHDRAWN (I wrongly claimed to refute Opus's castling line).
- job1/S-F3_WITHDRAWN.md records both retractions.
- Next: job 2 of area 1 (extreme numbers in FEN fields).

## 2026-11-16 (cycle 1, job 2)
- job2 DONE: 30 extreme-number FEN cases under ASan+UBSan. 0 crashes, 0 san lines, 0 illegal
  bestmoves. All 9 prediction points held (j2-10 was my own malformed 21-digit case).
- perft 2 vs python-chess: 10 comparable cases, 0 differences; engine stricter where they differ.
- S-C2 pushed earlier: CONFIRMS seat 01's S-F2 (impossible double check accepted, perft right).
- Next: job 3 of area 1 (position startpos moves, 1000 legal plies + one illegal move).

## 2026-11-16 (cycle 1, job 3 — area 1 complete)
- job3 DONE: 1000-ply legal list + illegal at ply 1/10/500/end + known case + garbage token.
  7/7 equal python-chess on plain AND ASan builds, 0 san lines. Prefix kept exactly (perft2 identity).
- ALL THREE area-1 jobs are now done.
- Next per brief 2(c): job 1 of area 1 AGAIN with SEED+10 (1111) and a NEW position set (R with SEED+10),
  and say in the report what differs from the first run.

## 2026-11-16 (cycle 2)
- Read FABLE_TO_swarm_2.md. RULE 1 (a zero needs a planted one) applied — and it FOUND A REAL
  DEFECT IN MY OWN RUNNER: readline() had no timeout, so a hung engine hung the harness and my
  "0 crashes/0 hangs" was not shown. Fixed with a queue+thread reader; plant now counted.
  Full 20k re-run with the fixed runner (job1/run_asan_v2) gives identical numbers. See RULE1.md.
- S-C3: CONFIRMS seat 19's 19-F5 (bench is stdin-only, argv ignored) with a control.
- Next: re-run job 1 with SEED+10 = 1111 and a new position set R (brief 2(c)).

## 2026-11-16 (cycle 2, area-1 round 2 = brief 2(c))
- Round 2 DONE: seed 1111, new R set (0 overlap). 20k cases, 0 crashes / 0 san lines / 0 illegal.
  85.44 % refused, 32 py-invalid = 23 F1 (extra token, now reproduced at scale) + 9 adjacent digits.
- PREDICTION 5 WAS WRONG (I said 0 F1 cases; my insert alphabet holds a space). Recorded, not edited.
- Next: cycle 3 board read, then claim the next unconfirmed peer finding (19-F1..F4, 29-F1/F2 remain).

## 2026-11-16 (cycle 3)
- S-C5: 29-F1's DIRECTION reproduced (NNUE off changes bench 13 tree 862329->907205, 1.16x nps).
  Explicitly NOT a reproduction of its profiler shares.
- S-F8 NEW: `setoption name X false` without the `value` word is silently ignored (uci.cpp:265
  name loop swallows the token). This broke my own runner first; fixed, v3 re-run identical numbers.
- Next: area 10 job 2 (recount deepseek6's longK report from its raw files).

## 2026-11-16 (cycle 3, area 10 job 2)
- DONE: recount of deepseek6 long58. The brief's named `REPORT_deepseek6_longK.md` /
  `tests_deepseek6_longK/` DO NOT EXIST on that branch (it has long1..long58); seat 10 had
  long56, so I took long58. All numbers reproduce EXCEPT "best moves changed 6-33", which is
  really 2-33 (FutilityDepth_p 2, FutilityDepth_m 4). S-F9.
- Next: area 10 job 1 (check a NEW unconfirmed peer finding; 19-F2..F4 and 29-F2 remain).

## 2026-11-16 (cycle 4 — HARNESS AUDIT after 19-F12 broadcast)
- 19-F12 (piped `quit` mid-search -> fabricated `bestmove` with 0 nodes) REPRODUCED on my build:
  piped `go depth 12` + quit on startpos -> `bestmove a2a3`, no info lines; with a 3 s wait ->
  `e2e4`, 56,720 nodes, depth 12. Not reported as my finding (seat 19 owns it).
- AUDIT: runner.py (job1, job2, job1r2, all S-F1..S-F9) sends one command at a time and reads to
  `bestmove`/`readyok` before continuing, and sends `quit` only after the last case -> NOT affected.
  Perft-based checks (castle_battery, perft2cmp, check_s01f2, job3) use `go perft`, which completes
  synchronously, and every number equals python-chess's -> not fabricated.
- AFFECTED and INVALID: check_s05f3.py (piped `go depth 10`) — scored nothing. Never recorded as a
  result. Rebuilt on ucio.py (waits for bestmove).
- New file: ucio.py — a waiting UCI driver for all future score-based work.
- Next: verify perft is not fabricated, re-verify a runner.py result with the waiting driver,
  then finish the S-F3 check.
- AUDIT COMPLETE, evidence `checks/verify_runner_not_fabricated.txt`: 12/12 sampled job1r2 cases give
  the same bestmove via runner.py and via the waiting driver, all with real info lines; control
  shows the piped form fabricating `a2a3` with 0 info lines. Perft unaffected (4,865,609 both ways).
- NOT affected: all job1/job2/job1r2 results, S-F1..S-F9, S-C2..S-C6, job3, castle_battery, perft2cmp.
- DISCARDS: one draft of check_s05f3 (piped go depth) — no numbers from it were ever recorded.
- S-C7: CONFIRMS seat 05 S-F3 (draw bites at H=91). Every score positively parsed; a missing
  parse raises MeasurementError and aborts with no verdict (seat 19's NaN warning applied).
  NOTE my cp values differ from theirs (381/271 vs 472/314) — same threshold, different options.
- S-A2 PARSER RE-AUDIT: found one real hole (check_s05f3 treated "no score printed" as "draw
  appeared" -> would have confirmed from nothing). Fixed to raise MeasurementError; live negative
  tests for s19f1/recount/s29f1 all fail loudly. Evidence checks/parser_audit.txt.
- S-C7 re-run AFTER the fix: CONFIRMS S-F3 at H=91, all 11 scores positively parsed.
- S-F10 NEW: the 9-ply-early draw is NOT universal — KRvK and KQvK flip to cp 0 at H=91, but
  KPvK flips only at H=99. Every score positively parsed; KRvKR was refused and gave no verdict.
- S-F11 NEW (goes beyond S-F3): the early draw is a HORIZON effect. Flip H = 96/95/92/91/89 at
  depth 4/6/8/10/12 — moves earlier as depth grows. So "9 plies early" is one point on a curve.
- S-A3 WARM/COLD AUDIT: no Clear Hash used anywhere. My runner pools 500 cases/process so later
  rows are warm: bestmove differs in 4/120 sampled cases warm-vs-cold, BUT illegal bestmoves are
  0 cold AND 0 warm, so the job-1 conclusion holds. Per-position bestmoves/node counts are labelled
  warm-dependent, not cold.
- S-F12 MY PREDICTION FAILED: I predicted the draw flip at depth 14 would be H~87; it is H=89,
  identical to depth 12. So the flip saturates by ~depth 12 — S-F11's "monotone with depth" is
  too strong and is corrected. What survives: flip is depth-dependent (96@d4 vs 89@d12/d14).
- S-F8 strengthened with a positive control: `UseNNUE value false` changes the depth-8 score
  26 -> 10, so the option works when written correctly; only the missing `value` word is silent.

## 2026-11-16 21:58Z CHECKPOINT (deadline 22:30)
Seat 11, area 1 (FEN input under ASan+UBSan). Branch for-fable-and-opus/swarm-11.
DONE (all pushed, raw evidence beside each):
- STEP 1 seat, STEP 2 build + honesty 4/4 (312866/862329/3024920/4865609).
- job1 (20k mutated FENs, ASan+UBSan, 0 crashes / 0 san lines, both sanitizer proofs).
- job2 (30 extreme-number FENs, perft2 vs python-chess 0 diffs), job3 (1000-ply moves list).
- job1 round 2 (seed 1111, new R set).
- Checks: S-C2 (seat 01), S-C3 (19-F5), S-C4 (19-F1 mech), S-C5 (29-F1 direction),
  S-C6 (19-F4 structure), S-C7 (seat 05 S-F3 threshold).
- Findings of mine: S-F1 extra token silently dropped (S-A4 narrows it to reporting only),
  S-F2 adjacent digits (known; proved harmless), S-F8 setoption without `value` word is silent,
  S-F9 deepseek6 long58 "6-33" is really 2-33, S-F10 early draw not universal,
  S-F11/S-F12 early draw is depth-dependent but SATURATES (my d14 prediction failed).
- Audits: S-A1 (19-F12 fabrication, my runner verified unaffected), S-A2 (parser NaN, one real
  hole fixed in check_s05f3), S-A3 (warm/cold: 4/120 bestmoves differ, 0 illegal either way).
- RULE1.md: planted controls for every zero I claim.
NEXT: continue area-1 work; push again by 22:30.
- S-F13 NEW: exhaustive ep-field matrix — 63 of 64 ep squares refused, only the legal `d6`
  accepted (perft 1 = 31 = python-chess). Ep validation is airtight; job 2's sampling generalises.
- S-F14 NEW: all 16 castling-rights subsets on 2 boards, 0 perft differences. Rights rule is
  exactly "king + matching rook on home squares"; accepted masks always match python-chess.
- S-F15 NEW: side-to-move (33 vs 31) and both counters (fullmove, halfmove) leave move generation
  untouched, all matching python-chess, 11/11 probes parsed. My first script had a false "all equal"
  over Nones — fixed to abort with MEASUREMENT FAILED; recorded in the finding.
- S-F16: piece-inventory rule matches board.cpp on 10 generated-FEN boundary cases (no defect).
  Recorded that my first hand-labelled FENs were wrong twice + pawns on rank 8 once — my errors,
  caught by generating FENs from intended counts.
- S-F17: job1's 20k headline replicates identically across 3 full runs incl. the final hardened
  runner (17130/2870/24/0/0), with .meta proving the setoption `value` syntax now takes effect.
- S-C8: CONFIRMS seat 21's 21-F2 — a refused FEN still answers readyok and the next search moves
  for the STALE side (g8f6 Black) vs d2d4 White when accepted. Two of my attempts failed first
  because a 7-field FEN is silently accepted (S-F1), so it never reached the refusal path.
- S-C9 CONFIRMS 21-F9: at halfmove 100 a MATE IN 1 is thrown away (f2f3, cp 0, 0 nodes) in both
  colours and all three go forms; at 99 all find d1d8/d8d1 mate 1. 6/6 vs 6/6. Serious defect.
- S-F18 NEW: mate-throwing boundary is exactly H=100 (mate 140 nodes at 95..99, f2f3 cp 0 at
  100..102). Hard 0-node adjudication — a SEPARATE mechanism from S-F10/S-F11's depth-dependent
  draw threshold.
- S-F19: located the exact cause of 21-F9 — src/search.cpp:2251 root_drawn omits the mate
  exception that is_draw() at :1302 deliberately has ("Checkmate on the hundredth half-move
  still wins"). Root returns score 0 before any search, so the mate is never played.
- S-P1 TEXT PATCH for 21-F9/S-F19: patches/fifty_mate_root.patch.txt applies with `patch -p1`
  without fuzz; honesty 4/4 unchanged; fault gone (6/6 H=100 mate now found); genuine draws and
  the checkmated root still adjudicate at 0 nodes (no regression).
- S-C10 SCOPES 24-F3: G position 90 is 0.04s cold / 0.02s warm on the RELEASE build (no outlier).
  Their 348s figure does not transfer here; likely TSan-specific. I do not claim their numbers are wrong.
- S-C11 CONFIRMS S-F2/24-C1: searchmoves naming no legal root move -> quoted info line +
  bestmove 0000 on a 20-move board; legal names do NOT trigger it (negative control asserted).
- S-C12 CONFIRMS S-F1(12)/24-C2: ucinewgame alone resets to startpos (6/e1f2 -> 20/e2e4 -> 6/e1f2
  after re-sending the position), with python-chess agreeing on both ends.

## 2026-11-16T22:18:45Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:45Z
- Seat 11 kept (branch for-fable-and-opus/swarm-11, folder forge-combo29/swarm/11). No new seat taken.
- Next: read FABLE_TO_swarm_3/4/5 (1 and 2 already read), then build the PC engine from file 5
  in a separate copy with -DFORGE_MATE_ALPHA_GUARD=1, check its bench numbers, then re-run my
  finds on the PC build under settings PC20 and label every finding with build + settings.

## 2026-11-16T22:21Z PC BUILD READY
- Read FABLE_TO_swarm_3, _4, _5 (1 and 2 read earlier). File 3 confirms my S-F3 withdrawal was RIGHT
  and says a patch for the base tree is NOT needed (so my S-P1 is superseded — see the note I will add).
  File 4: pins are DEFAULT-option numbers, sums are S14 — my honesty check was already correct.
- PC r15 built in /tmp/pcbuild from /tmp/pcbase (separate copy), sha256 of patch matches d6bd72c531f785f4.
  VERIFIED: default 4/4 pins; S14 242796/656517; PC20 278024/587276. All Threads 1.
- THREAD RULE: audited — every result I have recorded used Threads 1 (default or explicit). Nothing to retract.
- NEXT: re-run my finds on the PC build under PC20, labelling each with build + settings.
- RE-RUNS ON PC r15 UNDER PC20 (Threads 1), checks/rerun_pc20.txt:
  * 21-F9 / my S-C9+S-F18: REPAIRED (H=100 mate now found: d1d8, mate 1, 140 nodes; base gave f2f3 cp 0 0 nodes).
    My S-P1 patch is SUPERSEDED — file 3 says no base-tree patch is needed.
  * S-F8: HALF-repaired — now answers `unknown option UseNNUE false` instead of silence.
  * S-F1: STILL PRESENT — extra token still silently dropped on the PC build.
- S-F24: FEN layer on PC r15/PC20 is IDENTICAL to base on every probe (S-F2, S-F13, S-F14, S-F15, S-F16).
  So my FEN findings transfer unchanged to the PC. (Two FEN labels in this run were mislabelled by me again —
  the engine values are right; S-F16 has the correctly generated version.)
- S-F25: closed my own S-F24 mislabel. 8P+2R is LEGAL (2 rooks are original, no promotion needed) and
  8P+2Q is illegal — board.cpp's `promoted > 8-pawns` rule is consistent, engine correct, my labels wrong.
- S-F26: 05-F8/24-C3 NOT repaired on the PC — `go infinite` at a terminal root never volunteers a
  bestmove (6 s window, NO stop sent, ordinary-board control also NEVER). My first probe looked like a
  fix only because my pipeline sent stop; caught and corrected.
