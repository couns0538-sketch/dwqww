seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201

## 2026-11-16T21:12Z
STEP 1+2 done: SEAT 02; release build of 6b98f217 (sha256 e06310ec...) HONESTY PASS on all four numbers
(bench 11 312866 / 13 862329 / 16 3024920 / perft5 4865609). ASan+UBSan build sha256 b109a0a5... with both
required proofs (nm 35 __asan_ / 15 __ubsan_; planted fault counted 3 lines, control 0).

## 2026-11-16T21:40Z
S-C1 CONFIRMS seat 08's 08-F2 (movetime loses a fixed 9.4 ms to Move Overhead; zeroing the option removes it).
Re-audited with hard guards after seat 19's warning: an empty cell or a NaN now ABORTS the verdict, proven by
feeding it an empty list and a NaN (both abort, output in check08f2/RESULT.md).

## 2026-11-16T21:47Z
AREA 2 job 2 DONE: 5,000 race runs (stop / ponderhit / ucinewgame / setoption Hash / quit during a search,
1,000 each). 0 crash, 0 hang, 0 sanitizer lines, 0 illegal. S-F3: ponderhit on a non-ponder search is a
NO-OP, the search keeps running (1,000/1,000). REPORT_job2.md.

## 2026-11-16T21:55Z
AREA 2 job 1 DONE on the THIRD harness. v1 was withdrawn (pipelined stdin -> 19-F12 fabricated bestmoves,
HARNESS_INVALIDATION.md); v2 discarded (waited on unbounded searches). v3 result: 2,000 sequences, 5,827 go,
5,827 bestmove, 0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves, 0 missing readyok/uciok.
S-F2 empty `searchmoves` -> `bestmove 0000` on a board with 20 legal moves (67 cases). S-F4 `go wtime N`
with Black to move (or `go btime N` with White to move) sets NO limit and searches until stopped
(src/uci.cpp:118-121). REPORT_job1.md (v1 kept as REPORT_job1_v1_WITHDRAWN.md).

FINDINGS so far: S-F1 (argv ignored — this one is now also confirmed by seat 10 as 10-C1, so it is known;
kept for the record), S-F2, S-F3, S-F4, S-C1 (CONFIRMS 08-F2).

Next: cycle step 1 (read board, newest FABLE_TO_swarm), then AREA 2 job 3 (every option at its min, max,
min-1, max+1, a word and nothing, between and during searches), then job 1 again with seed 211 and a new R set.

Exact next command:
  cd /agent/repos/dwqww && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git ls-tree FETCH_HEAD forge-combo29/soak_all/ | grep FABLE_TO_swarm | tail -2
