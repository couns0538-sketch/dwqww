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


## 2026-11-16T21:34:59Z
CHECKPOINT PUSH (owner asked for a push every 30 min). All three area-1 jobs done and pushed earlier. Now: check of seat 05's S-F3 written as checks/CHECK_s05f3.md -> CONFIRMS its numbers (flip at H=91, depth 10) but REFUTES its framing: the cliff moves with depth (first zero at H=96/95/92/91/89 for depth 4/6/8/10/12 = 101-D, minus one when quiescence reaches deeper), so it is the search horizon, not an early fifty-move rule. Files: checks/check_s05f3.py, checks/check_s05f3_depth.py, checks/s05f3/*, checks/s05f3_depth.log.
Next: area 1 job 1 again with SEED+10 and a fresh R set (cycle rule 2c).

## 2026-11-16T21:36:25Z
job 1 SECOND run (SEED 111, fresh R2 with 3,155 positions) done: 18,670 refused (93.35 %) / 1,330 accepted / 42 accepted-but-invalid / 0 crashes / 0 sanitizer lines / 0 illegal bestmoves of 1,288 judged. CONTROL PASS, accept/refuse STABLE. Sharper than run 1: ALL 42 invalid cases are the known adjacent-digit rule, zero other causes (run 1 had 1 double-check case). Refusal order by mutation identical at both seeds. Report: REPORT_job1b.md. New findings S-F14, S-F15.
DELIVERY: FINDINGS.md now holds S-F1..S-F15 and S-C1, S-C2; every job1/job1b/job2/job3/checks raw file and both .patch.txt files are pushed with this commit (patches: job2/fifty_move_mate.patch.txt, job1/sanitizer_proof/planted_fault.patch.txt).
Next: cycle -> check another seat's NEW finding (seat 17 S-F1/S-F2 searchmoves-0000 is still unchecked and nobody has a C line for it).

## 2026-11-16T21:37:09Z
MEASUREMENT-INTEGRITY response to seat 19's warning, done and audited. (1) Wrote audit_integrity.py which re-reads every committed raw file and asserts, per record, that the line each verdict depends on was actually FOUND: job1 20000/20000 records have BOTH readyok and bestmove (0 invalid), job1b 20000/20000 (0 invalid), job2 asan 29 cases (0 invalid), job2 results_fix 5 (0 invalid), job3 4 (0 invalid), check_s11_f1 7 (0 invalid). Result in INTEGRITY.txt: 'no record passes a verdict on a missing value'. (2) Found and FIXED a real hole of my own in the new checks/check_s17f1.py before running it:  (the old bestmove-not-in-0000-or-empty test) would have passed a MISSING bestmove as a confirmation; replaced with bm_of() which fails hard and prints VERDICT: INVALID. (3) Audited and cleared my S-C1 (check_s11_f1): every case records readyok=True and an integer perft1_nodes, and the control case deliberately differs (30 vs 20), so the CONFIRMS was measured, not vacuous. (4) Also audited the FEN refusal tables: a dead process cannot read as 'accepted' in job1/job1b (crashed is a separate flag AND both readyok and bestmove are asserted); note runner_extreme.py in job2 DOES set refused=False on a dead process, but it also sets crashed=True and the audit rejects those records — 0 such records exist in the committed runs.
NEW CHECK: S-C3 CONFIRMS seat 17 S-F1 (searchmoves with no legal name answers bestmove 0000 + an info string, while the control returns d2d4 and naming e2e4 returns e2e4), and partially confirms its S-F2 with a correction: ASan+UBSan report nothing on that path, so root_candidates.front() at search.cpp:2640 yields a garbage Move rendered as 0000, not a sanitizer-catchable read. Report checks/CHECK_s17f1.md.
Next: continue the cycle with the remaining time; next push by 22:30 UTC must carry everything.


## 2026-11-16T21:37:16Z
STRENGTHENED the integrity audit with a synthetic NEGATIVE TEST: the audit is now fed a fabricated record that accepted a FEN with no readyok and no bestmove, and it must raise exactly 2 integrity failures. Output: 'negative test: ... raised 2 integrity failures (expected 2) -> AUDIT WORKS'. So 'clean' now means the audit was shown to be able to catch the failure seat 19 described, not merely that it printed nothing. Re-ran on all raw files: still 0 invalid records. Also fixed a shell-quoting slip that blanked one parenthetical in the previous STATUS block.

## 2026-11-16T21:40:39Z
REGRESSION-TESTED my own patch (closes the caveat I flagged): job2/asan/regress_fifty_patch.txt, base release build vs patched build, 5 boards x 2 go modes. Genuine fifty-move positions at halfmove 100 and 150 (KQ v K, KR v K, K v K) still answer cp 0 on the patched build, so the draw is still seen; the cost is 0.4-0.6 ms wall and 200-1,792 nodes instead of 0 (K v K stays 0 nodes, as it should); and the mate-in-one board at halfmove 100 returns mate 1 where the base returns cp 0. No regression. Finding S-F16.
Next: continue the cycle.

## 2026-11-16T21:42:51Z
S-F5 now shown to cost REAL GAMES, not just analysis: job2/asan/gameplay_fifty.txt runs the brief's S14 settings (every setoption followed by isready read to readyok) and three clock modes. Mate-in-one board at halfmove 100: bestmove f2f3, cp 0, 0 nodes under go wtime 1000, go wtime 10000 AND go movetime 500. Same board at halfmove 99: a1a8, mate 1, 1344 nodes under all three. No problem lines (no unknown option, no invalid value). This raises S-F5 from an analysis curiosity to a game-play defect and strengthens the case for fifty_move_mate.patch.txt, which is regression-tested (S-F16).
Next: cycle.

## 2026-11-16T21:43:46Z
SELF-CORRECTION, mechanism at search.cpp:2640 WITHDRAWN. My earlier S-C3 said 2640 is reached with an empty root_candidates; that was an INFERENCE from the printed bestmove 0000, not an instrument. I have now built my own -D_GLIBCXX_DEBUG engine (sha256 581159a4...) and run it: the CONTROL (empty front() under the same flag) ABORTS with 'Error: attempt to access an element in an empty container' at /usr/include/c++/13/debug/vector:460, proving the checking is on; and NONE of my six searchmoves cases aborts (no_names, bogus_name, illegal_pair all return 0000 with exit 0 and no diagnostic). This agrees with seat 17's control-flow markers (EARLY_PATH cand=0 legal=20, no PAST_EARLY) and with seat 07's identical instrument plus its withdrawal of its own S-F2. RESOLVED: bestmove 0000 comes from the empty-root early path at 2253; the observable is a fabricated 'info ... score cp 0 nodes 0' line plus 0000 on a board with 20 legal moves, confirmed by three seats. My ASan-silence remark was right and is now stated as 'consistent with there being no read at all'. Files: checks/CHECK_2640_RESOLVED.md, checks/check_2640_instrument.py, checks/s2640/. FINDINGS: S-C3 restated as observable-only, new S-C4 as the refutation of my own mechanism.
Next: continue the cycle until 22:30 UTC.

## 2026-11-16T21:44:55Z
DELIVERED the one-page patch summary Opus asked for: PATCH_SUMMARY_fifty_move.md (104 lines) in this order — the bug (and that it costs real games: f2f3/cp 0/0 nodes under go wtime 1000, go wtime 10000 AND go movetime 500 at halfmove 100, vs a1a8/mate 1/1344 nodes at halfmove 99), the one-line change at search.cpp:2251 with the exact before/after code, the FOUR commands with their pasted before/after output (halfmove 99 unpatched = patched = mate 1/126 nodes; halfmove 100 unpatched = cp 0/0 nodes/f2f3, patched = mate 1/126 nodes/a1a8), the regression table for genuine draws with its cost (0.2-0.6 ms, at most 1,792 nodes, K v K still 0 nodes), and the four pins before and after (all unchanged). Commands saved as job2/four_commands.txt.
ALSO: finished the conservative variant as job2b — fifty_move_mate_conservative.patch.txt, honesty ALL PASS (honesty/fix3/summary.txt), regression table identical in verdict to the one-line version (genuine draws still cp 0, K v K still 0 nodes, mate found). Applies with patch -p2 --fuzz=0 and the applied tree is byte-identical to the source I tested. S-F18. Both patches kept exactly as they were.
FINDINGS.md now: S-F1..S-F18, S-C1..S-C4. This is the complete delivery for the 22:30 deadline.
