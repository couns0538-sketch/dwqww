seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201

## 2026-11-16T21:12Z
STEP 1+2 done: SEAT 02, release build of 6b98f217 (sha256 e06310ec...), HONESTY PASS on all four numbers
(bench 11 312866 / 13 862329 / 16 3024920 / perft5 4865609). ASan+UBSan build sha256 b109a0a5... with both
required proofs (nm 35 __asan_ / 15 __ubsan_; planted fault counted 3 lines, control 0).

## 2026-11-16T21:19Z
S-C1 CONFIRMS seat 08's 08-F2: `go movetime T` loses a fixed 9.4 ms to Move Overhead at BOTH T=50 (median
40.56) and T=200 (190.62) and loses under 1 ms at both when Move Overhead is 0 — so it is the overhead
subtraction, not a fraction of the movetime. check08f2/RESULT.md.

## 2026-11-16T21:33Z
AREA 2 job 2 DONE (valid harness, see below): 5,000 runs, 1,000 each of stop / ponderhit / ucinewgame /
setoption Hash / quit during `go infinite` or `go depth 30` at a random 0-50 ms delay.
0 crashes, 0 hangs, 0 sanitizer lines, 0 illegal bestmoves, 1,000/1,000 readyok and follow-up search after
every interrupt. Findings: ponderhit on a non-ponder search is a NO-OP and the search keeps running
(1,000/1,000). Report in REPORT_job2.md.

## 2026-11-16T21:35Z — HARNESS INVALIDATION (19-F12 broadcast)
job 1 v1's numbers are WITHDRAWN: that runner piped all lines and closed stdin, so its bestmoves came from
the known fabricated-`bestmove` path (I reproduced it: piped `go depth 12`+`quit` gives 0 info lines and
`bestmove a2a3`; interactive gives 12 info lines and `e2e4`). Details: HARNESS_INVALIDATION.md.
job 2 and check08f2 are unaffected (both read to `bestmove` before sending anything else).
Re-running job 1 now with run_sequences_v2.py (interactive, answer-before-next-line).

Next command:
  cd /agent/repos/dwqww/forge-combo29/swarm/02/job1 && python3 run_sequences_v2.py /agent/repos/base/forge-combo29/build-asan/forge seqs.jsonl out2 4
