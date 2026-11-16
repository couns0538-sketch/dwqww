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

## 2026-11-16T21:34:42Z
HARNESS AUDIT after the coordinator's broadcast (19-F12, quit/EOF mid-search -> fabricated bestmove a2a3, 0 nodes):
my harness is NOT affected and no recorded result is invalidated. Evidence, committed, control_quit_midsearch.out:
- A: `go depth 12` + immediate quit -> `bestmove a2a3`, 0 info lines  (broadcast reproduced)
- B: same search, quit after 2 s -> 12 info lines, `bestmove e2e4` at 56,720 nodes  (matches their numbers)
- C: `go perft 4` + immediate quit -> `nodes 197281` (complete)
- D: `go perft 5` + immediate quit -> `nodes 4865609` (complete)
- E: stdin closed right after `go perft 4` -> `nodes 197281` (complete)
- F: a perft run emits 0 `bestmove` lines at all.
Reason: `go perft` is synchronous — the full divide + `nodes N` block is written before the next command is read, so
stdin termination cannot truncate it. My engine_perft.py reads every line up to the `nodes N` line and never sends
quit while a search runs (quit is sent only after the last position, and the runner closes stdin then). Area 3 is
therefore perft-only and outside 19-F12. I do not claim 19-F12 as mine.
TIME WINDOW: working continuously to 22:35 UTC, push at ~22:04Z and ~22:34Z plus at every job part.
job1 reference perft still running: 3571/5000 python-chess positions done (4 workers), engine side finished at 26.3 s.

## 2026-11-16T21:36:18Z
FINDINGS.md pushed now as ordered (2 findings: 23-F1 the 19-F12 boundary is synchronous-perft, 23-F2 python-chess 1.11.2
has no Board.perft()). job1 reference perft 3939/5000 python-chess positions; engine side long done (engine_R.jsonl,
5000 rows, 26.3 s, meta records exe path + sha256 e06310ec... + id name "Chess Engine Forge 6.4.24 candidate").
Next push 22:04Z with the comparison table if the reference finishes; if not, the partial counts + STATUS go anyway.
