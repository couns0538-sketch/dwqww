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

## 2026-11-16T21:35Z

Job 1 DONE (S-F1): perft 1..4 on 5,000 R (SEED 301), 20,000/20,000 equal to python-chess, move sets identical.
Job 2 DONE (S-F2, S-F3): 314 special positions, perft 1..4 all equal. Class B absent from R+G (my filter bug first,
recorded) -> 6,000-game hunt (14 real) + constructor (320 verified).
HARNESS AUDIT vs 19-F12 (pipelines quit behind a live search -> fabricated bestmove): reproduced; my perft/bench
numbers immune (inline in the UCI loop) and RE-PROVED with honesty2.py; ep_divide.py replaced.

## 2026-11-16T21:37Z

PARSE AUDIT vs seat 19's NaN warning: `assert_measured.py` now fails loudly on a missing/NaN/zero result, with
negative controls that both fail. Two real defects of mine found and recorded (honesty.sh's dead grep pattern;
divide_sets.py's summary never saved). Every recorded number passes the assertion.

## 2026-11-16T21:50Z — CHECKPOINT

New since the last push:
- **03-C1: CONFIRMS seat 13's S-F1.** Both halves measured with my own harness on their R_1301 set: their engine
  file vs my engine run = 20,000/20,000 equal; my python-chess run vs my engine run = 20,000/20,000 equal
  (sums 113,231 / 2,678,512 / 77,182,397 / 2,260,227,623). Their `raw_ref.txt` being byte-identical to
  `raw_engine.txt` is the expected consequence of 0 differences — I traced it (run1 ref side killed, exit 143;
  run2/ref_par.py regenerated it in 616.8 s) rather than assuming a copy.
- **S-F4:** 320 constructed en-passant-pin positions, engine root move set = python-chess exactly (320/320) and a
  control passes 320/320 (delete the pinning slider -> the same ep capture becomes legal, engine still matches).
  Goes beyond 23-F6's three hand-built positions.
- Job 3 (perft 5 on 200 R + 30 G): ENGINE side done — sums 5,644 / 137,090 / 4,013,465 / 119,698,590 /
  3,925,995,728, 0 restarts, 0 error lines; perft-1 move sets identical on all 230. python-chess depth-5 side
  RUNNING now (4 workers); the depth-5 comparison is NOT done and REPORT_job3.md says so.
- Job 1b (cycle step 2c, SEED 311): prediction pushed alone; engine perft 1..4 done (sums 112,193 / 2,606,301 /
  74,557,281 / 2,159,914,969, 0 restarts, 0 error lines; 0 duplicate FENs vs the SEED-301 set). python side pending.

Runs: job3 python perft 5 (4 workers), then job1b python perft 1..4.
Next: finish job3 depth-5 comparison, then job1b, then the next cycle.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job3 && tail -1 py_all230.log && python3 ../job1/compare.py eng.json py_all230.json d.txt && python3 ../assert_measured.py perft py_all230.json 5 230`
