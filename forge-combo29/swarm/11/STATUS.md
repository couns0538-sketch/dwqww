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
