# SEAT 03 STATUS

- seat: 03
- area: 3 (MOVE GENERATION against python-chess)
- branch: for-fable-and-opus/swarm-03
- seed: 301

## 2026-11-16T21:06:34Z

seat claimed, starting STEP 2 build

## 2026-11-16T21:14Z

HONESTY: all four pins MATCH (bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609).
Build used: /home/ubuntu/build-rel/forge, g++ 13.3.0, -DFORGE_MARCH=native, sha256 68825bd5...
Board read: FABLE_TO_swarm_1 (no corrections; its ALREADY KNOWN list is respected). Seats 13, 23 are the other
area-3 seats and have no FINDINGS.md yet, so nothing to check yet.

Job 1: prediction pushed alone (95cd8fe3d). R set = 5,000 FENs, SEED 301, written by job1/gen_R.py.
Engine side DONE (perft 1..4, 12.7 s, 0 restarts, 0 error lines). python-chess side runs in background
(job1/py_R.log). Job 2 prediction pushed alone; class filter done on R+G and on a 40k R pool (see job2).

Runs: job1 python-chess perft 1..4 on 5,000 R (about 10 min); job2 ep_hunt.py (class B, 6,000 games).
Next: compare job 1, then job 2 perft 1..4 on the selected special positions.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job1 && tail -2 py_R.log && python3 compare.py eng_R.json py_R.json job1_diffs.txt > job1_table.txt 2>&1; cat job1_table.txt | head -20`
