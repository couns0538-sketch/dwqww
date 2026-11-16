seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201

## 2026-11-16T21:12Z
STEP 1+2: SEAT 02; release build 6b98f217 sha256 e06310ec..., HONESTY PASS (bench 11/13/16 = 312866 / 862329 /
3024920, perft 5 = 4865609). Sanitizer build sha256 b109a0a5... with both required proofs (nm 35/15, planted
fault counted 3 lines, control 0).

## 2026-11-16T21:40Z
S-C1 CONFIRMS 08-F2 (movetime loses a fixed 9.4 ms to Move Overhead; zeroing the option removes it). Re-audited
after seat 19's warning: an empty cell or a NaN now ABORTS the verdict (proven by feeding it both).

## 2026-11-16T21:47Z
JOB 2 DONE: 5,000 race runs, 0 crash / 0 hang / 0 san / 0 illegal. S-F3: ponderhit on a non-ponder search is a
no-op and the search keeps running (1,000/1,000). REPORT_job2.md.

## 2026-11-16T21:55Z
JOB 1 DONE (third harness). v1 WITHDRAWN for 19-F12 (HARNESS_INVALIDATION.md), v2 discarded. v3: 2,000
sequences, 5,827 go = 5,827 bestmove, 0 crash / 0 hang / 0 san / 0 illegal / 0 missing readyok-uciok.
S-F2 empty `searchmoves` -> `bestmove 0000` on a board with 20 legal moves (67 cases).
S-F4 `go wtime N` with Black to move (or `go btime N` with White to move) sets NO limit (src/uci.cpp:118-121).

## 2026-11-16T22:02Z
JOB 3 DONE: 82 options x 6-7 values, 550 cases, idle and during a search. 0 crash / 0 san / 0 illegal.
Out-of-range spins: 116/116 refused with the documented line. Spins and checks refuse a word 79/79.
S-F5: the button `Clear Hash` answers `invalid value` when sent WITH a value (even `value 0`), though the
no-value form clears correctly. REPORT_job3.md.

ALL THREE AREA-2 JOBS ARE DONE. FINDINGS: S-F2, S-F3, S-F4, S-F5 (NEW), the withdrawn v1 numbers, and
S-C1 (CONFIRMS 08-F2).
Next: cycle item 2(c) — job 1 again with seed 211 and a fresh R position set, saying what differs from run 1;
then check another seat's unchecked NEW finding if one is left.

Exact next command:
  cd /agent/repos/dwqww && git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | wc -l && git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git ls-tree FETCH_HEAD forge-combo29/soak_all/ | grep FABLE_TO | tail -1
