seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201

## 2026-11-16T21:10Z
Seat claimed (SEAT 02). Release build of 6b98f217 in worktree /agent/repos/base, g++-13, cmake Release,
sha256 e06310ec...  HONESTY PASS on all four numbers (bench 11 312866 / 13 862329 / 16 3024920 / perft5 4865609).

## 2026-11-16T21:12Z
ASan+UBSan build done (sha256 b109a0a5...). Both required proofs recorded in sanitizer/NOTES.md:
nm counts 35 __asan_ / 15 __ubsan_, and a planted fault (heap over-read "sanprobe" + signed overflow
"ubprobe" on a scratch copy at /tmp/forge-fault) counted by the same runner: clean 0 lines, fault 3 lines,
fault with the probes removed from the input 0 lines.

## 2026-11-16T21:20Z
AREA 2 job 1 DONE. 2,000 random UCI command sequences (seed 201), one fresh engine process each:
crashes 0, hangs 0, sanitizer lines 0, illegal bestmoves 0, missing readyok 0, missing uciok 0,
5,827 go lines all answered by 5,827 bestmove lines. Tables from make_tables.py, raw in job1/out/.
Two NEW findings: S-F1 (engine ignores argv entirely; `forge bench 13` prints NOTHING, use stdin — this
silently breaks argv-driven harnesses) and S-F2 (empty `searchmoves` -> `bestmove 0000` on a board with
20 legal moves). Report: REPORT_job1.md.

Next: cycle step 1 (read board), then AREA 2 job 2 (races: stop/ponderhit/ucinewgame/setoption/quit
during a running search, 1,000 each).

Exact next command:
  cd /agent/repos/dwqww && git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort | tr '\n' ' '
