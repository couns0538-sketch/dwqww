# STATUS swarm-23

- seat: 23
- area: 3 (MOVE GENERATION against python-chess)
- branch: for-fable-and-opus/swarm-23
- seed: 2301
- started: 2026-11-16T21:06:22Z

## 2026-11-16T21:06:22Z
Seat claimed. Next: build engine commit 6b98f217 at ../base, run honesty check (bench 11/13/16, perft 5).

## 2026-11-16T21:25:13Z
Done: seat 23 claimed; build at 6b98f217 (Release, x86-64-v4, GCC 13.3.0) honesty 4/4 (bench 11/13/16 = 312866 /
862329 / 3024920; perft 5 = 4865609). HONESTY.txt pushed. Area 3 = MOVE GENERATION.
job1: prediction.txt committed alone before measuring. R_2301.fens = 5000 positions from random legal games
(SEED 2301, one every 7 plies, 367 games), all python-chess valid. Engine perft 1..4 over all 5000: DONE, 26.3 s
(engine_R.jsonl). python-chess reference perft 1..4: RUNNING, 4 parallel workers, ~1150/5000 at 21:30Z.
Note: python-chess 1.11.2 has no Board.perft(); I wrote count()/divide() in pych_perft.py (startpos 1..5 = 20 / 400 /
8902 / 197281 / 4865609 matches the known values).
Board read: handoff FABLE_TO_swarm_1.md read, no STOP, no corrections. No FINDINGS.md yet from any area-3 seat
(03/13/33/53/21 checked) so there is no NEW finding to check this cycle.
Next: finish the reference, run compare_perft.py, write REPORT_job1.md, FINDINGS, push.
