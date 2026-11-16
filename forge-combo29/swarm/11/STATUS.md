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
