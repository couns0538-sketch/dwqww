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
