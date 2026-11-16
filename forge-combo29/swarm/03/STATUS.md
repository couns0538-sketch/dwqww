# SEAT 03 STATUS

- seat: 03
- area: 3 (MOVE GENERATION against python-chess)
- branch: for-fable-and-opus/swarm-03
- seed: 301

## 2026-11-16T21:06:34Z

seat claimed, starting STEP 2 build

## 2026-11-16T21:14Z

HONESTY: all four pins MATCH (bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609).
Build: /home/ubuntu/build-rel/forge, g++ 13.3.0, -DFORGE_MARCH=native, sha256 68825bd5...
Board read: FABLE_TO_swarm_1 (no corrections; ALREADY KNOWN respected).

Job 1 DONE: perft 1..4 on 5,000 R positions (SEED 301) -> 20,000/20,000 measurements equal to python-chess, 0
diffs, 0 refused, 0 crashes; root move SETS also identical (0 missing, 0 extra). REPORT_job1.md, FINDINGS S-F1.
Job 2 DONE: 314 special positions (A 100 / B 14 / C 91 / D 9 / E 100) -> perft 1..4 all equal, move sets identical.
Class B had 0 occurrences in R+G (my filter had a bug first — recorded in REPORT_job2.md) so I hunted 6,000 games
(14 real hits) and built a constructor (320 verified). FINDINGS S-F2, S-F3. REPORT_job2.md.

## 2026-11-16T21:35Z

HARNESS AUDIT after seat 19's broadcast (19-F12: pipelined `quit` behind a running `go` gives a fabricated
`bestmove` at 0 nodes). Reproduced on my build. My `go perft`/`bench` numbers are immune (both run inline in the
UCI loop: src/uci.cpp:489, :590) and were RE-PROVED with a read-until-token harness (`honesty2.py`, all four pins
MATCH). One harness (`job2/ep_divide.py`) did pipeline `quit`; replaced by `ep_divide2.py`, verdicts identical.
Full detail: HARNESS_AUDIT.md.

Runs: job3 python-chess perft 5 on 200 R + 30 G (background, 4 workers); check13 python perft 1..4 on seat 13's
R_1301 set (background) to CONFIRM seat 13's S-F1 with my own harness (planted-fault control done: my comparison
catches a fake engine that drops 1 and invents 1 move, and reports the real engine clean).

Next: finish check13 (S-C line), then job 3 perft 5 comparison, then job 1 re-run with SEED 311 (cycle step 2c).

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/check13 && tail -2 py.log && python3 ../job1/compare.py eng.json py.json diffs.txt | head -12`
