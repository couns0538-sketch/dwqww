## 2026-11-16T21:09Z

seat 01
area 1 (FEN INPUT under ASan + UBSan)
branch for-fable-and-opus/swarm-01
seed 101

Status: seat claimed, base commit 6b98f217 checked out on local branch swarm-seat. Next: STEP 2 build + honesty check.

## Commands run (raw)

- `git remote get-url origin | sed "s#//[^@/]*@#//#"` -> `https://github.com/couns0538-sketch/dwqww`
- `bash ~/take_seat.sh "DeepSeek V4.1 Flash"` -> `SEAT 01`

## 2026-11-16T21:14:04Z
job 1 done and pushed: 20,000 mutated FENs under ASan+UBSan. 18,715 refused / 1,285 accepted / 39 accepted-but-invalid (38 known digit rule + 1 new double-check case) / 0 crashes / 0 sanitizer lines / 0 illegal bestmoves. Both sanitizer proofs recorded in job1/sanitizer_proof/. Report: REPORT_job1.md. Findings S-F1..S-F4 in FINDINGS.md.
Next: cycle step 1 (read the board), then area 1 job 2 (extreme numbers in FEN fields).

## 2026-11-16T21:17:52Z
job 2 done: 34 extreme-FEN cases on ASan+UBSan, 17 refused / 17 accepted / 0 crashes / 0 sanitizer lines / perft 2 equal to python-chess in all 17 judged. REAL FAULT found and patched: halfmove>=100 short-circuits the root as a draw (0 nodes) and misses a mate-in-one (S-F5..S-F7); patch fifty_move_mate.patch.txt keeps all four honesty numbers. One self-correction recorded in REPORT_job2.md (a mislabelled pawn-rank case). Also wrote S-C1 CONFIRMS S11-F1 (junk after the sixth FEN field).
Next: cycle -> area 1 job 3 (position startpos moves, 1000 plies, illegal move at ply 1/10/500).
## 2026-11-16T21:30:46Z
job 3 done: 1,000-ply list accepted (perft 1 = 16 = python-chess), illegal move at ply 1/10/500 keeps the legal prefix (20/32/6, all equal to python-chess), 0 sanitizer lines, 0 crashes, setup 0.03 s. Extra edge cases: list through a threefold repetition accepted, list past checkmate refused at that move. Brief's known case (perft 1 = 29) reproduced. Findings S-F9..S-F13. All three area-1 jobs are now done.
Next: cycle -> area 1 job 1 again with SEED+10 and a fresh R set, per cycle rule 2(c); before that, re-read the board for any NEW finding to check.

