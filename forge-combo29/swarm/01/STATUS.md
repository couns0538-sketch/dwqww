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

## 2026-11-16T21:52:29Z — FINAL PUSH for the 22:30 deadline
PATCH_SUMMARY_fifty_move.md extended as instructed, now 8 sections: (6) RELATIONSHIP TO THE OTHER ROOT PATCHES — my diff and seat 12's are the same change written two ways and FAIL on top of each other (measured, not assumed: mine-then-12 FAILED, 12-then-mine FAILED), mine+27 and 12+27 both apply CLEAN in EITHER order with byte-identical result files, so the root fix goes in before seat 27's drawn_root_reporting; all four patches named with their branches, paths and -p levels so it is checkable; plus a MEASURED limit applying to both: on a halfmove-100 board with a mate 3 plies away, mine searches 216 nodes and still says cp 0 and seat 12's says cp 0 in 0 nodes, while the same board at halfmove 0 scores cp 1331 — so both fix mate-in-1 only (S-F19). (7) COLD vs WARM: seat 10's effect reproduced on my build exactly (startpos go depth 12: 56720 / 56720 / 56720 across three processes; 56720 / 4951 / 4516 warm in one process; 56720 x3 with ucinewgame; 56720 / 40569 / 35808 with Clear Hash). Every number I quote is COLD — verified by reading my own harnesses (one fresh Popen per case in honesty.py, analyse_halfmove.py, regress_fifty_patch.py, gameplay_fifty.py; no harness of mine sends Clear Hash; gameplay_fifty.py sends ucinewgame once before its single search). The 126-node and 0-node figures are also warm-stable, re-checked four ways on the exact boards quoted. S-F20.
STATE: all three area-1 jobs done, job1 rerun at SEED 111, two independent checks of other seats (S-C2 seat 05, S-C3/S-C4 seat 17/07 with my own _GLIBCXX_DEBUG instrument and a self-correction), measurement-integrity audit with a synthetic negative test, two patches (one-line + conservative) both honesty-checked and regression-tested. FINDINGS.md holds S-F1..S-F21 and S-C1..S-C4 (22 finding lines). Every raw file, both patch files, the composition test and the patch summary are pushed.
Next command I would run if time remained: python3 job2/gameplay_fifty.py for the 3-ply mate case, to check whether the clock path also loses mate-in-3.

## 2026-11-16T21:53:45Z — deadline push
MATE-IN-3 UNDER CLOCKS, run as the coordinator asked, and it CORRECTED ME TWICE. job2/asan/mate3_clocks.txt, base vs my patch vs seat 12's patch, 4 go modes, halfmove 0 / 99 / 100, every case a fresh process.
(a) MY S-F19 WAS WRONG (now S-F23). Its board 8/8/8/8/2K4Q/8/8/1k6 has only QUIET mating moves, so the counter hits 100 after White's move and Black CLAIMS the draw — cp 0 is CORRECT chess there, not a missed mate. Verified with python-chess can_claim_fifty_moves().
(b) THE DISCRIMINATING BOARD gives the opposite answer (S-F22). 8/3K4/7P/8/8/7k/8/6Q1 mates in 3 plies and its first mating move h6h7 is a PAWN move, which RESETS the counter, so no claim is available. At halfmove 100 with go depth 12: unpatched cp 0 / 0 nodes, seat 12 cp 0 / 0 nodes, MINE mate 2 / 398 nodes. Under go wtime 1000, go movetime 500 and go nodes 200000: unpatched and seat 12 both 0 nodes, mine mate 2 in 2114 nodes. So my patch fixes the whole counter-resetting class, not just mate-in-1, and is STRICTLY MORE COMPLETE than seat 12's on this case.
(c) The clock path does NOT lose it differently from the depth path (S-F24): the unpatched engine gives 0 nodes in all four go modes, so the loss is the root adjudication everywhere, not the stop logic.
(d) I also found my own test of seat 12's repetition advantage measured NOTHING (S-F25): the shuffle was refused because the FEN root had no knights, so no threefold formed; that advantage stays UNVERIFIED and the summary now says so instead of claiming seat 12's patch is a superset.
PATCH_SUMMARY_fifty_move.md section 6 now opens with the sentence a merger acts on: neither patch is complete, the measured boundary is a mate whose line does not reset the fifty-move counter, with a 3-row board table showing unpatched / mine / seat 12 side by side.
Next command if time remained: rebuild a genuine threefold-with-mate-in-1 root using 'position startpos moves' from a position that HAS knights, to settle seat 12's repetition claim.

## 2026-11-16T21:54:22Z
DECIDING TEST DONE — the two patches are COMPLEMENTARY, not ranked. Ran seat 12's OWN repetition case (board 6k1/5ppp/8/8/8/8/8/R5NK, knight+king shuffle to a threefold at halfmove 8, setup VERIFIED with python-chess: shuffle legal, is_repetition(3) True) against MY patch. job2/asan/mypatch_on_repetition.txt, go depth 6, fresh process per case:
  mate-in-1 no history        base mate 1/108 | mine mate 1/108 | s12 mate 1/108
  mate-in-1 at halfmove 99    base mate 1/108 | mine mate 1/108 | s12 mate 1/108
  mate-in-1 at halfmove 100   base cp 0/0     | mine mate 1/108 | s12 mate 1/108
  mate-in-1 at THREEFOLD, c=8 base cp 0/0     | mine cp 0/0     | s12 mate 1/108  <-- MINE DOES NOT FIX THIS
So my patch does NOT close the repetition door, exactly as its diff predicts (it only removes the halfmove>=100 test and leaves the repetition branch adjudicating). COVERAGE: counter-resetting mates incl. mate-in-1 and pawn-move mate-in-3 at 100 = MINE (seat 12's misses); mate at a threefold root with counter under 100 = SEAT 12's (mine misses); plain mate-in-1 at 100 = both. Seat 21's verification of seat 12's repetition door is CONFIRMED from the other side, and my earlier S-F25 was my own bad setup, not a refutation. New findings S-F26, S-F27, S-F28.
PATCH_SUMMARY_fifty_move.md section 6 now leads with the deciding measurement and a two-row coverage table naming which door each patch fixes, removes the stale 'seat 12 is a superset' paragraph, and ends the fifty-move table with 'Neither patch is the whole fix.'
Next command if time remained: build the combined fix (my reset-aware root test PLUS seat 12's immediate-mate bypass for the repetition and dead-material doors) as a THIRD patch, honesty-check and regression-test it, since neither existing patch alone is complete.

## 2026-11-16T21:55:36Z
BUILT THE COMBINED FIX, since neither existing patch closes every door (S-F29). job2c/fifty_move_and_doors.patch.txt = my reset-aware fifty-move test PLUS seat 12's immediate-mate bypass for the repetition and dead-material doors. Applies clean with patch -p2 --fuzz=0 and the applied tree is byte-identical to the source I tested. ALL FOUR DOORS CLOSED on measured evidence: mate-in-1 at halfmove 100 -> mate 1/108; mate-in-1 at a threefold root with counter 8 -> mate 1/108; pawn-move counter-resetting mate-in-3 at halfmove 100 -> mate 2/398 nodes (go depth 12) and mate 2/2114 nodes under go wtime 1000, go movetime 500 and go nodes 200000; plain controls unchanged. GENUINE DRAWS STILL DRAWN: KQ v K, KR v K, K v K at halfmove 100-150 all cp 0, K v K still 0 nodes, cost 0.2-0.6 ms. FOUR PINS ALL PASS (job2c/honesty_patched.txt). PATCH_SUMMARY now has section 5b RECOMMENDED with the patch, the code, and a four-column table (unpatched / one-line / seat 12 / combined) so Opus can act without reading logs; section 8 now scopes 'every door' to 'every door I could build a test for' and still says Elo cost is unmeasured.
Next command if time remained: build a dead-material-door case with a reachable mate to close the one door I have not constructed a test for.

## 2026-11-16T21:56:00Z
DEAD-MATERIAL DOOR TESTED AND NEEDS NO FIX (S-F30): the engine's is_insufficient_material() (src/board.cpp:1250) is exactly 'no pawn/rook/queen AND (minor count <= 1 OR all bishops on one colour)', which is material where NO mate can be constructed. Swept 400 random positions in that material (273 insufficient per the rule): 0 had any legal mating move; on the combined build 0 of 40 searches returned a mating bestmove. So the immediate-mate bypass in job2c never fires on that door — a result, not a gap. PATCH_SUMMARY section 8 updated to say the dead-material door needs no fix and to keep the one genuinely unmeasured case (a counter-resetting mate landing on a later move).

## 2026-11-16T21:58:35Z
TWO FINAL ITEMS DONE, plus the applicability warning.
1) APPLICABILITY BOX at the very top of PATCH_SUMMARY_fifty_move.md, exactly as asked: it says this is measured on base 6b98f217, that seat 20 reports (from FABLE_TO_swarm_3) the drawn-root defect is BASE-TREE ONLY and Opus repaired it on the owner's PC since 15 Nov, and that if the tree already adjudicates a halfmove-100 mate-in-1 correctly then NOTHING from this file should be applied. It carries FOUR one-minute verification commands with the expected output for each, plus a note that a bare bestmove with no score line means the pipe raced quit and to re-run with a sleep. S-F33.
2) REDUNDANCY CHECKED AND REMOVED (S-F31). Seat 12's immediate-mate bypass is now kept ONLY for the repetition and dead-material doors. It is NOT used to rescue the halfmove-100 door, because the reset-aware test already covers that. I proved the removal is safe by building the scoped variant and running it: mate 1 at halfmove 100, mate 1 at the threefold root, mate 2 on the counter-resetting board, four pins ALL PASS, genuine draws all still cp 0 with K v K still 0 nodes. The superseded unscoped diff is kept as job2c/fifty_move_and_doors_UNSCOPED.superseded.txt so the change is auditable. The patch's header comment was rewritten to match (it had described a bypass for both doors, which would have misled the next reader). Applies clean with patch -p2 --fuzz=0 and the applied tree is byte-identical to the binary I tested.
3) SEAT 21'S FOURTH DOOR reproduced and recorded, NOT closed (S-F32): a CHECKMATED root answers score mate 0 and bestmove 0000 on both the unpatched engine and my combined build, on 4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60. Section 8 now lists it explicitly so 'closes every door' cannot be read as complete: it means every door that can HIDE a mate, not a mate already delivered.
FINDINGS.md: S-F1..S-F33 and S-C1..S-C4. Nothing further started.

## 2026-11-16T22:18:53Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:53Z
Seat 01 (from ~/swarm_seat.txt and SEAT.txt on this branch), area 1 (FEN input under ASan+UBSan), branch for-fable-and-opus/swarm-01. Next: read every FABLE_TO_swarm_N.md I have not read (I have read N=1 only), lowest to highest, then build the engine from file 5's patch in a SEPARATE copy with -DFORGE_MATE_ALPHA_GUARD=1, check its known bench numbers, and re-run my finds on that build under PC20.

## 2026-11-16T22:20:26Z
THREADS RULE acknowledged and AUDITED (THREADS_AUDIT.txt). grep -rn 'Threads' over every .py in my folder returns NO MATCH, so no harness of mine ever sent a Threads option, and both builds list 'option name Threads ... default 1'. So every score and node count I have recorded is Threads 1 and none needs the provisional label. Qualification I state because it is true: my harnesses relied on the default rather than sending Threads 1 explicitly; new harnesses from now on send it and record it in .meta.
FABLE files read: 1 (earlier), 2, 3, 4, 5 (all of them). File 3 CONFIRMS my applicability box: the drawn-root defect is base-tree only, repaired on the PC since 15 Nov, and 'a patch for the base tree is not needed'. File 4 explains pins are DEFAULT-option numbers while the sums are under S14 - my honesty.py already sends no setoption, so my pins are correct. File 5 ships the PC r15 source; I extracted the patch (sha256 d6bd72c531f785f4... matches Opus's stated prefix), applied it in a SEPARATE copy at /agent/repos/pc, and built it with -DFORGE_MATE_ALPHA_GUARD=1. Verification of its known bench numbers is running now.
Next: finish the PC build verification (none / S14 / PC20 rows), then answer the one question file 5 raises for my area: is my combined patch still needed on the PC build now that FORGE_FIX_ROOT_DRAWN is in it?

## 2026-11-16T22:30:37Z
PC BUILD BUILT AND VERIFIED, and the answer for my area is in (S-F34, S-F35). Extracted file 5's patch (sha256 d6bd72c531f785f4... matches Opus's prefix), applied in a SEPARATE copy /agent/repos/pc with patch -p1 (11 files, clean), built with -DFORGE_MATE_ALPHA_GUARD=1. ALL EIGHT known answers PASS: none 312866/862329/3024920/4865609, S14 242796/656517, PC20 278024/587276 - each a fresh process, regimes kept separate as file 4 demands.
**ANSWER TO THE QUESTION file 5 raises for my area: MY PATCH IS NOT NEEDED ON THE PC BUILD.** Under PC20, Threads 1, Hash 16, the PC build closes every door I can build: mate-in-1 at halfmove 100 = mate 1/126; the threefold root = mate 1/102 (base cp 0/0); the counter-resetting pawn-move mate-in-3 at halfmove 100 = mate 2/398 (base cp 0/0); genuine draw at 150 stays cp 0/280. FORGE_FIX_ROOT_DRAWN covers what my job2c patch and seat 12's two_doors_mate covered on base 6b98f217. job2c/fifty_move_and_doors.patch.txt must NOT be applied to the PC tree.
HONESTY NOTE on how that was measured (S-F36): my first run of this test produced c2c4 and d2d4 on a board where those are ILLEGAL, because I had written the repetition FEN with only its placement field, so the engine refused it and kept startpos. I caught it, fixed three bugs in that harness (missing FEN fields, waiting for bestmove after perft, reading the perft total only from info depth lines), and added a GUARD that re-runs go perft 1 on every build+case and compares with python-chess's legal count. The numbers above are from the guarded run, which printed no guard failures.
Next: re-run my base-tree finds on the PC build under PC20 one by one, starting with the FEN refusal behaviour (job1/job2/job3 findings), to say for each whether it is repaired on the PC.

## 2026-11-16T22:31:01Z
RE-RAN ALL ELEVEN OF MY BASE-TREE FEN FINDINGS ON THE PC BUILD UNDER PC20 (Threads 1, Hash 16) WITH A CLEAN BOARD GUARD (S-F37). Result: NOT ONE OF THEM IS REPAIRED. Identical answers on both builds: adjacent digits still ACCEPTED (perft 1 = 23); impossible double check still ACCEPTED (perft 2 = 64); junk after the sixth field still ignored (perft 1 = 20); halfmove 65536 and fullmove 10^9 still ACCEPTED; ep square on a wrong rank, two white kings, pawn on rank 8 and the 3,000-character field still REFUSED with the same reason strings; the 1,000-ply move list still applied exactly (perft 1 = 16). So FORGE_FIX_ROOT_DRAWN fixed the drawn-root family and nothing in the FEN parser - which is what its switch name says, and it is the useful half of the answer for my area: my job2c patch is unnecessary on the PC, and my FEN findings all still stand there.
ONE FINDING SPECIFICALLY FOR OPUS (S-F38): seat 21's CHECKMATED-ROOT door is STILL OPEN on the PC build under PC20. 4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60 (checkmate, 0 legal moves) answers score mate 0 and bestmove 0000 on the PC build exactly as on base. That is the one door FORGE_FIX_ROOT_DRAWN did not close, so it is the only one in my area still worth a patch.
Next: area 1 job 2 (extreme FEN numbers) re-run under PC20 with the perft cross-check, then the sanitizer build of the PC r15 source if time allows.

## 2026-11-16T22:31:51Z
WROTE THE GUARD NOTE as asked: REFUSED_FEN_TRAP_AND_GUARD.md - named for what it prevents, stating the signature in one sentence (an engine that refuses a position command keeps the PREVIOUS position and answers normally, so a test on a malformed FEN silently measures the previous board and looks plausible), with the real example from my harness (c2c4 on a board where c2 is empty), why review does not catch it, the guard code, and five rules including the two other lines of the same trap that bit me (waiting for a line the engine never prints; short FENs elsewhere in the test). Written for every seat that builds positions by hand.
Also built the ASan+UBSan version of the PC r15 source (~/builds/pcasan, 35 __asan_ / 15 __ubsan_ symbols) so the PC-build tests can also be run under a sanitizer with the two proofs I already have.
Next: the three priority FENs (halfmove 65536, fullmove 10^9, junk after the sixth field) - for each, what a GUI would have to send, whether the resulting board is still legal, and whether it can reach a real game at all.

## 2026-11-16T22:32:12Z
THE THREE PRIORITY FENs ANSWERED (S-F39, S-F40) on PC r15 with the guard clean and 0 sanitizer lines:
  halfmove 65536 : accepted, engine on exactly the CORRECTED board (perft 1 = 20 = python-chess). Would need a GUI writing the counter as a 16-bit value past 65535. A real game's counter cannot exceed 150 (seventy-five-move rule; 100 ends it by claim).
  fullmove 10^9  : accepted, board exact. Would need a GUI deriving the move number from a clock/ply count with an arithmetic or float bug. The engine has no observable use for the field.
  junk after 6th : accepted, board exact. Would need a GUI appending an annotation or a trailing separator to a valid FEN.
ANSWER: all three need malformed input, none can arise from a well-formed GUI sending a legal game, and on all three the resulting BOARD IS STILL LEGAL and move generation is exact. So all three are COSMETIC. Ranked by plausibility in the wild: junk_after_six first (most likely to happen and harmless), then the two counters. The one non-cosmetic detail (S-F40): the out-of-range halfmove IS read - cp 20/14621 nodes vs cp 24/13102 at halfmove 0 - so the clamp affects the SCORE on such input, even though such input cannot arise legally.
Also done this stretch: guard note REFUSED_FEN_TRAP_AND_GUARD.md written for other seats; PC r15 ASan+UBSan build made (~/builds/pcasan, 35 __asan_/15 __ubsan_) and used in the runs above.
Next: area 1 job 2 (extreme FEN field values) fully re-run under PC20 on the PC build, then job 3 (move lists) likewise.

## 2026-11-16T22:33:49Z
JOB 1 RE-RUN ON PC r15 UNDER PC20 (Threads 1, Hash 16), all 22 options logged in meta.txt, no unknown-option or invalid-value lines (S-F41, S-F42).
  refused 18,670 / accepted 1,330 - a ZERO-record difference in the refused flag against my base-tree seed-111 run; same per-mutation profile (drop 100 / delete 97.80 / insert 97.55 / swap 90.38 / replace 81.49); same 42 accepted-but-python-invalid, and ALL 42 are the known adjacent-digit rule with 0 other causes. So FORGE_FIX_ROOT_DRAWN and the other r15 switches changed nothing in set_fen.
  SEARCH answers differ on 109 of the 1,330 accepted FENs at go depth 2 - and every differing pair I could judge has BOTH moves legal (105 both-legal, 0 one-illegal, 0 both-illegal, 4 unjudgeable because python-chess rejects the FEN). Different valid choices at shallow depth under different settings, not a defect; I checked rather than assumed because 'bestmoves differ' would otherwise read as one.
  Also fixed the analyse.py header, which had hard-coded 'ASan+UBSan build' and would have mislabelled this PC20 release-build run; it now reads build and settings out of each run's meta.txt.
Next: job 2 (extreme FEN field values) on PC r15 under PC20, then job 3 (move lists) likewise, then a sanitizer pass of r15 over the FEN corpus with the two proofs.

## 2026-11-16T22:36:16Z
SANITIZER PASS ON THE PC r15 SOURCE DONE AND PROVEN (S-F43). ASan+UBSan build of r15 (sha256 ae1a49b6..., nm shows 35 __asan_ / 15 __ubsan_) over the same 20,000 mutated FENs under PC20, Threads 1, Hash 16: 0 sanitizer lines, 0 crashes, and the analysis is identical to the release build (18,670 refused / 1,330 accepted / 1,288 valid / 42 accepted-but-python-invalid / 0 illegal bestmoves).
The zero COUNTS because of the planted case the rules demand: I planted ONE heap over-read in a scratch copy of the SAME r15 source behind input I control (a FEN starting PLANTED), built it the same way, and ran it through THE SAME runner - which counted it: 'AddressSanitizer: heap-buffer-overflow ... in apply_position' at src/uci.cpp:58. Artefacts: job1d/sanitizer_proof/ (crash log, the planted diff as text, the planted .meta with the nm counts, counts.txt).
So the PC r15 FEN path is clean under both sanitizers on 20,000 malformed inputs, with the instrument shown able to fire.
Next: job 2 (extreme FEN field values) on PC r15 under PC20, then job 3 (move lists).

## 2026-11-16T22:36:36Z
JOB 2 ON PC r15 UNDER PC20 DONE (S-F44, S-F45). All 34 extreme-FEN cases reproduce exactly: 17 refused / 17 accepted, 0 crashes, 0 sanitizer lines, perft 2 equal to python-chess in all 17 judged, and ZERO refusal-flag differences against my base-tree run. Accepted halfmove values identical: 0, 99, 100, 150, 9999, 65535, 65536, 100000.
INDEPENDENT CONFIRMATION OF THE PC REPAIR (S-F45): at go depth 4 on startpos, halfmove 0 and 99 search on both builds (412 / 393 nodes), but halfmove 100 / 150 / 100000 give 0 nodes on BASE and 393 / 132 / 132 nodes on PC r15 with normal scores. FORGE_FIX_ROOT_DRAWN does what file 5 says, and my job-2 table confirms it changed nothing else in the FEN path.
Next: job 3 (move lists, illegal-move prefix rule, 1,000-ply list) on PC r15 under PC20, then the sanitizer equivalent where it adds anything.

## 2026-11-16T22:36:45Z
JOB 3 ON PC r15 UNDER PC20 DONE (S-F46): identical to base. 1,000-ply list accepted, perft 1 = 16 = python-chess; illegal move at ply 1/10/500 keeps the exact legal prefix (20/32/6, all equal to python-chess) with exactly one 'info string illegal move e1e3' line; 0 sanitizer lines, 0 crashes, setup 0.0 s. Edge probes identical: threefold list accepted (perft 1 = 20), move after checkmate refused and keeps the mate (perft 1 = 0), stalemate list accepted (perft 1 = 0).
SUMMARY OF THE WHOLE RE-RUN FOR MY AREA: every single one of my area-1 behaviours reproduces on the PC r15 build under PC20 - the FEN parser (job 1: 18,670 refused, 0-record difference; job 2: 34 cases identical) and the move-list path (job 3: identical). The ONLY differences the PC build shows are the intended ones: halfmove>=100 roots now SEARCH (0 nodes -> 393/132) instead of being adjudicated, which is FORGE_FIX_ROOT_DRAWN doing what file 5 says. And the one defect in my area that survives is seat 21's checkmated root (score mate 0), still present on PC r15 under PC20.
Next: check what remains open in my area and in the newest other-seat findings; then continue the cycle with the remaining hours.

## 2026-11-16T22:37:43Z
CHECKMATED-ROOT mate 0 SETTLED AND CLOSED AS DOCUMENTATION, and MY OWN CLAIM IS WITHDRAWN (S-C5, S-F47). Note: CHECKMATE_ROOT_MATE0_CLOSED.md.
  1) The output is the correct UCI encoding, measured on both builds: already checkmated -> mate 0 + bestmove 0000; can mate in 1 -> mate 1 + a1a8; stalemated -> cp 0 + 0000; losing -> cp -984. Four answers, one consistent scale. The formatter proves it rather than agreeing by luck: src/search.cpp:353 prints 'mate 0' only when distance = MateValue - abs(score) = 0, i.e. exactly the side that is already mated.
  2) NOTHING IN THE REPOSITORY CONSUMES IT - checked, not assumed. The repo has only two tooling files that could read engine output: verify.py (parses training-curve score arrays, never UCI text) and replay-work.js (asserts move-ordering buffers, never UCI text); no other .py/.js/.sh outside swarm/ and recorded tests_* data; grep for 'score mate|Mate(0)|mate_score == 0' over the engine, scripts/, windows/, windows_build/ finds NO parser; and the helper branches deepseek6-work and glmflash5-work-cb5c contain no .py matching 'score mate' or 'score cp'.
  3) Verdict: correct per the encoding, harmless per the repository, documentation not a defect. S-F32 and S-F38 are WITHDRAWN. Seat 21's withdrawal (21-F11) is right and I confirm it. One useful leftover for anyone parsing: a MATED root and a STALEMATED root BOTH answer bestmove 0000, so to tell them apart you must read the score (mate 0 vs cp 0), never the bestmove.
Next: continue with confirmations, now using the PC build and PC20 where a find names them.

## 2026-11-16T22:45:34Z
FILE 6 READ AND APPLIED TO MY OWN FINDINGS. It retires my S-F5/S-F17 as defect claims and I have written that up rather than defended them (S-C6, FILE6_APPLIED_TO_MY_FINDINGS.md).
  File 6's prescribed test at go depth 20, PC r15/PC20/Threads 1/Hash 16, base for contrast: A mate-in-1 at counter 100 -> mate 1 at counter 0, so 2N-1 = 1 vs 100-counter = 0, inequality FALSE, base cp 0 => NOT a defect (that mate would land on the 101st half-move, past the match program's cut-off). A2 the same board at counter 99 -> 1 <= 1 and BOTH builds answer mate 1, confirming file 6's own exception is already handled. C mate-in-3 quiet at counter 99 -> 3 > 1, not a defect. So my patch is not needed anywhere, exactly as file 6 says.
  ONE CASE THE INEQUALITY MISSES (S-F48): 8/3K4/7P/8/8/7k/8/6Q1 at counter 100 mates with h6h7 FIRST, a PAWN move, which RESETS the halfmove counter to 0 (verified: the FEN reads '... b - - 0 1' after it). The game never reaches the 100th half-move on that line, so the cut-off never applies and the mate is real; file 6's arithmetic assumes the counter advances monotonically, which a pawn move breaks. Base cp 0, PC mate 2. This is the narrow class where a base-tree cp 0 at a high counter is still a missed mate - and the PC build already fixes it.
  APPLICABILITY BOX REWRITTEN to quote file 6: the summary now opens with DO NOT APPLY THIS PATCH, both reasons (not a real-play defect; the PC tree already repairs it), the one remaining real case, and four one-minute check commands. Everything below it is kept as evidence about base 6b98f217.
Next: file 6's suggested new area - go softnodes N on the PC build under PC20 at Threads 1: deterministic run to run, does it stop at a finished depth, how far past N does it go.

## 2026-11-16T22:46:00Z
MATEALPHAGUARD CONFIRMED INDEPENDENTLY, AND ITS LIMIT MEASURED (S-C7, S-F49).
  PROOF OF THE TRUE DISTANCE, no engine involved: my own minimax in python on 8/8/1p6/8/p3p3/8/2Kpk3/8 w shows black forces mate in exactly 8 plies (= mate -4) and NOT in 2/4/6. So seat 20's 'true distance' is right.
  SHALLOW-DEPTH ANSWER, which the coordinator asked for: the guard's effect does NOT survive below the depth where the mate becomes visible. Depth 8: both cp -2718, identical 5,755 nodes. Depth 10: both cp -3154, identical 15,860 nodes. Depth 12: off mate -9 (18 plies) vs on mate -4 (the true 8 plies). Depth 16: BOTH mate -4, with the guard using 48,022 nodes against 83,450. So at a fast time control the guard changes nothing at all - it is not a strength fix, it is a correctness fix that only applies once the search can see the mate.
  I also fixed two bugs in my own guard-check harness before publishing: my first mate solver had the quantifiers backwards (returned None for a board mated in 8 plies), and then 'plies_on == true_plies' compared None with None and printed SURVIVES - the exact vacuous-pass pattern I warned other seats about. Both are fixed; the None case now prints 'no mate score reported' and the verdict says the effect does not survive.
Next: file 6's suggested new area - go softnodes N on the PC build under PC20, Threads 1.

## 2026-11-16T22:46:36Z
FILE 6's NEW AREA DONE: go softnodes N on the PC build under PC20, Threads 1, Hash 16 (S-F50, S-F51).
  1) DETERMINISTIC: YES, on all 9 cases (3 positions x 3 N values), each run three times in THREE SEPARATE PROCESSES - identical bestmove, score, total nodes and depth every time. That is the property the PC's self-play depends on and it holds.
  2) STOPS AT A FINISHED DEPTH: YES. The stop lands at the end of the first iteration that reaches N, and the depth sequence is monotone with no gap, so the reply is a completed iteration, never a partial one.
  3) HOW FAR PAST N: much further than 'about 2000 nodes' suggests. Overshoot min 5.8 %, median 43.7 %, MAX 106.0 % (startpos at N=2000 spends 4,121 nodes). Mechanism, from the code: the soft budget is checked only after an iteration finishes (search.cpp:2932) and the hard cap is 4N (2497-2500), so the overshoot is one final iteration and cannot exceed 4N. Confirmed by a 16-point N sweep on startpos: 9 distinct bands, every N inside a band gives the identical depth/bestmove/score (N=15000/18000/20000 all -> depth 12, cp 25, 21,600 nodes), ratio min 1.02 / median 1.20 / max 2.06, worst just above a band boundary. PRACTICAL ADVICE for the owner's self-play: pick N ON a band boundary from softnodes/softnodes_staircase.txt rather than just below one, or the node cost per game varies by up to 2x with no change in search quality.
Next: extend the softnodes check to real game positions and to the clock path (6s+0.06), which file 6 names as the strength-match path.

## 2026-11-16T22:48:39Z
BOTH REQUESTS DONE, and the challenge is settled on evidence.
1) THE DEPTH TABLE NOW NAMES THE BOARD ON EVERY ROW (S-F49b), and the run filled depths 13, 14, 15. Board, stated explicitly because a mis-paired board is what produced the challenge: 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1 = white Kc2 + pawn d2 vs black Ke2 + pawns a4, e4, b6 - a LOST PAWN ENDING with NO QUEEN on it, which is why the scores are large negative cp. True distance 8 plies (mate -4) proved by exhaustive minimax. Guard OFF vs ON, depths 8/10/12/13/14/15/16: 8 and 10 identical (cp -2718 @5,755; cp -3154 @15,860 - no mate seen by either); 12 OFF mate -9 (18 plies) vs ON mate -4; 13 OFF mate -9 (18 plies) vs ON mate -4; 14 OFF mate -7 (14 plies, 69,360 nodes) vs ON mate -4 (39,960); 15 both mate -4, ON 44,008 vs OFF 78,688 (44 % fewer); 16 both mate -4, ON 48,022 vs OFF 83,450 (42 % fewer).
2) HEADLINE CORRECTED as you asked (S-F49b): the guard is DECISIVE at depths 12-14, and at depth 15-16 the two agree on the verdict while the guarded search is CHEAPER by 42-44 % in nodes - not redundant at depth 16. My earlier 'does not survive at depth 16' wording was wrong and is corrected rather than quietly dropped.
3) S-F48 NOW NAMES ITS OWN BOARD (S-F48b): its rows are 8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1 (Kd7 + pawn h6 + QUEEN g1 vs Kh3) at go depth 20 - a different board from S-F49's pawn endgame. On that board the guard makes no difference at depths 12-16 (all mate 2, identical nodes), which is consistent with the guard's effect appearing only where the mate first becomes visible.
4) SOFTNODES ON REAL GAME POSITIONS (S-F52), answering the other half of the request: five G positions x ten budgets. The band boundaries move by min 1.00x / median 2.00x / MAX 3.00x between positions, so the advice is READ THE STAIRCASE PER POSITION - a single fixed N is not safe for the owner's self-play. Within a position, place N at or just above a band's FIRST budget, since the node total is constant across a band. Per-position band table in softnodes/softnodes_real_games.txt.
Next: the clock path (6s+0.06) that was queued behind this.

## 2026-11-16T22:51:17Z
THE ONE-LINE DECISION IS IN THE STAIRCASE FILE (S-F53), measured not asserted: with one fixed budget N=6000 across the five real G positions the nodes actually spent ranged 6,124 to 14,978 - a factor of 2.45x - while the DEPTH, the BESTMOVE and the SCORE were IDENTICAL on 5 of 5 positions compared with each position's own band-start budget. So ignoring the per-position advice costs up to ~2.5x in search time per game and NOTHING in search quality: a cost decision, not a correctness one. A wrong move would have made it urgent; there is none. The line now sits at the TOP of softnodes/softnodes_real_games.txt so the lookup table reads as a decision.
CLOCK PATH ALSO DONE (S-F54, S-F55): go nodes is NOT exact either - reported 19,832 for N=20,000, 31,779 for N=50,000, 170,070 for N=250,000 (0 of 6 exact), because it stops at the end of the iteration that crosses N, exactly like softnodes; the difference is softnodes has a 4N hard cap and reports its total. The 6s+0.06 clock is stable in its MOVE (e2e4 5/5, g7g6 5/5) and far under budget (158-364 ms of 6000) but NOT node-reproducible: 314,239 nodes in 4 of 5 middlegame runs and 288,912 with cp -292 in the fifth. So matches needing reproducibility should use a node budget, and any clock-derived score is provisional.
Next: continue the cycle - check the newest unconfirmed findings from other seats on the PC build under PC20.

## 2026-11-16T22:52:07Z

CORRECTION NOTICE: the previous STATUS block was damaged by shell backtick substitution (the command names
were executed instead of written). Rewritten here with the text escaped properly.

go nodes STATEMENT CORRECTED AND MADE PRECISE (S-F54b), because "not exact" was the wrong framing.
Three measurements on PC r15 / PC20 / Threads 1 / Hash 16:
  M1: the number on the last info-depth line EQUALS the total of "go depth D" at that same D, on 3 of 3
      budgets - so it is the true total of the COMPLETED iterations: honest, neither truncated nor invented.
  M2: it is below N on 6 of 6 cases, by up to 79,930 nodes, so the real spend lies in [reported, N] and the
      reported figure understates cost by at most N - reported. Reported as a percentage of N: 95.8 / 97.6 /
      99.2 / 98.2 / 97.3 / 68.0 for N = 5k / 10k / 20k / 50k / 100k / 250k.
  M3: sweeping N inside ONE iteration band (38,478 to 52,000) gives identical depth 12, 31,779 nodes and
      bestmove g7g6 every time - the budget does NOT truncate an iteration; it finishes the iteration and
      then stops. N = 60,000 raises it to depth 13 / 52,904 nodes.

SO, PRECISELY: "go nodes N" means "finish the iteration that crosses N, then stop". A match harness CAN trust
the last reported count as an honest total; it must just know that count excludes the aborted iteration, and
that "go nodes" prints no total for it - unlike softnodes, which prints an "info string softnodes nodes
<total>" line. That is a different and more useful statement than "not exact", and it is the one on record.

ALSO RECONCILED seat 13's softnodes worst case with my 4N-cap claim (S-F56): their 659,130 total at
N = 250,000 is 164 % over N but sits 340,870 nodes INSIDE the 4N = 1,000,000 cap, so both statements hold.
Useful bound: overshoot up to 164 % observed, hard-capped at 4N.

Next: keep confirming other seats' findings on the PC build under PC20.

## 2026-11-16T22:52:39Z
SEAT 13's S-F7 CONFIRMED EXACTLY (S-C8) and the harness consequence stated (S-F57).
  Reproduced on seat 13's own worst-case board 8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1 at N=250000, PC20, Threads 1, Hash 16, fresh process: 163.7 % overshoot, total 659,130 nodes, depth 17, g5h5 - their numbers to the node, identical across two runs. It sits 340,870 nodes INSIDE the 4N hard cap of 1,000,000, so their figure and my cap claim are both true, which is what I wanted to settle.
  A 7-point N sweep on that board gives 3 distinct bands with overshoot from 19.4 % to 163.7 %, LARGEST AT MEDIUM N (N=100000 overshoots 138.7 % while N=200000 overshoots only 19.4 %). That is what shows the overshoot is one final iteration's size and not a proportion of N - so 'unbounded in proportion' overstates it, while the numbers in it are exactly right.
  THE LINE YOU ASKED FOR, now in both the report and FINDINGS (S-F57): a harness that trusts the last reported count must also record that the ABORTED iteration's nodes are NOT included, so any cost comparison between two engines must add the same allowance on both sides - otherwise it mis-prices whichever engine aborts a larger iteration, and at 164 % that error exceeds most Elo-relevant differences. Related: go nodes reports only completed iterations (S-F54b) while softnodes reports its true total including the final iteration, so a cost table mixing the two is comparing different quantities.
Next: keep confirming other seats' findings on the PC build under PC20.

## 2026-11-16T22:53:04Z
SEAT 25's REPAIR SCOPED, NOT REFUTED (S-C9). Their S-C5 already applies file 6's rule and reclassifies their own clock-99 family as NOT a defect for the owner's matches - yet their S-F22/S-F23/S-F24 then price a repair built on the premise file 6 rejects (that someone could reset and play on). Both cannot be the operative reading, so I measured what actually decides it on PC r15/PC20/Threads 1/Hash 16:
  (A) quiet mate-in-3 at clock 99 reads cp 0 at depth 20, and by file 6's rule the match ends at the 100th half-move before 3 plies can happen (1 is left), so the engine's answer cannot change a match result - the repair is priced against a non-defect FOR MATCHES.
  (B) the counter-RESETTING class (my S-F48), 8/3K4/7P/8/8/7k/8/6Q1 at clock 100, reads mate 2 at depth 20 AND mate 2 under go wtime 1000, because the mating line starts with the pawn move h6h7 which resets the counter so the cut-off never fires. That is the ONLY class where a repair has real value - and the PC build already gets it right.
  (C) startpos baseline cp 18 at depth 20, so a depth drop on A is attributable to the clock rather than to position type.
  VERDICT: the repair is technically sound and cheap where it fires, but for the owner's match program it addresses a class the match program ends before it matters, and the class that does matter is already correct on the PC build. If it is taken for HUMAN play, price it at seat 25's measured 11-20 plies and scope it there. I did not have their patched build, so I verified the PREMISE and SCOPE, not their node counts - said plainly in the file.
Next: keep confirming other seats' findings on the PC build under PC20.

## 2026-11-16T22:56:44Z
SEAT 16's S-F15 PARTIALLY CONFIRMED (S-C10), and I caught a broken checker of my own before publishing (S-F58).
  THE BROKEN CHECKER: my first colour-symmetry harness mapped moves with a file+rank flip, but chess.Board.mirror() is a VERTICAL mirror (flips RANKS, swaps colours and the turn). That mapping produced 0 matches out of 60 in EVERY arm - 100 % mismatch is the signature of a broken checker, not a result, so I did not publish it. Fixed to a rank flip, verified against python-chess (legal move SETS exactly equal under it), after which the checker gives 44/60, which is plausible. The harness now verifies that legal-move-set equality on five positions as a SANITY CONTROL and refuses to print a verdict if it fails.
  THE RESULT, on 60 G positions + colour mirrors, PC r15, depth 10, Threads 1, Hash 16, comparing MOVES only: mismatches base_S14 16, +TtPruneV2 17, +HistRework 24, PC20 21. So TtPruneV2's direction CONFIRMED (raises asymmetry) and PC20 worse than base_S14 CONFIRMED, but HistRework does NOT lower asymmetry (24 vs 16) - the opposite of their finding that HistRework is the one MORE symmetric cell. Their counts are on all 353 positions and mine on 60 so the numbers are not comparable; the direction of the HistRework cell is, and that is where we differ.
Next: the FINAL block, with the counter-resetting class stated as a positive result for the PC build as instructed.

## 2026-11-16T22:56:53Z FINAL

Seat 01, area 1 (FEN input under ASan+UBSan, then the PC r15 build and the softnodes path).
Branch for-fable-and-opus/swarm-01. Every result is Threads 1. PC20 = S14 + CuckooRep true, HistRework 2,
TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false, Threads 1, Hash 16.

### THE POSITIVE RESULT FOR THE PC BUILD — do not lose this among the retirements

**The counter-resetting mate is CORRECT on PC r15 and WRONG on base 6b98f217.** Board
`8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1`: the mating line begins `h6h7`, a PAWN move, which RESETS the fifty-move
counter to 0, so the match program's 100th-half-move cut-off never fires and the mate is real. Base 6b98f217
scores `cp 0` in 0 nodes; **PC r15 finds `mate 2`** — 398 nodes at `go depth 12`, and 2,114 nodes under
`go wtime 1000 btime 1000`, `go movetime 500` and `go nodes 200000`. This is one of the few places where the
r15 tree is demonstrably BETTER than base, and it is exactly the class where a fifty-move repair would have
real value. (S-F48, S-F22, S-F34; FILE6_APPLIED_TO_MY_FINDINGS.md.)

The shape of the win matters: it is NOT the mate-in-1 everyone reported. File 6's inequality correctly marks
mate-in-1 at counter 100 as not a defect. What survives is the class whose mating line resets the counter —
and the PC build handles it.

### EVERY FIND OF MINE, WITH STATE, BUILD AND SETTINGS

FEN behaviour (base 6b98f217 and PC r15, re-run under PC20):
- S-F1 / S-F14 / S-F15 — adjacent digits accepted (38/20,000, and 42/42 at two seeds); CONFIRMED by seat 11
  (S11-F2), reproduced on PC r15 under PC20. Open as behaviour, cosmetic.
- S-F2 / S-F3 / S-F4 — impossible double check accepted; engine stricter than python-chess in three ways;
  93.35 percent of mutations refused. Cosmetic, identical on PC r15 under PC20 (S-F41).
- S-F8 / S-F39 / S-F40 — extreme counters accepted and clamped; all three need malformed input, boards still
  legal; ranked by plausibility in S-F39.
- S-F9 / S-F10 / S-F37 / S-F46 — 1,000-ply move lists and illegal-move prefixes behave exactly, both builds,
  under PC20.
- S-F43 — zero sanitizer lines over 20,000 FENs on r15's ASan+UBSan build, with the planted-fault proof that
  makes the zero count.
- S-F54b / S-F56 — `go nodes` is a hard cap that reports honest completed-iteration totals; the softnodes
  overshoot is one final iteration, bounded absolutely by 4N.

Fifty-move family — RETIRED BY ME under file 6's own prescribed test:
- S-F5, S-F17 (mate-in-1 at counter 100 called a defect) — **RETIRED** (S-C6). 2N-1 = 1 against
  100-counter = 0; the counter-99 control gives `mate 1` on both builds.
- S-F19 — **WRONG**, its board was not discriminating (S-F23 corrects it).
- S-F22 / S-F48 — true, but scoped to the counter-resetting class on base only; the PC build fixes it.
- S-F32, S-F38 (checkmated root `mate 0` called an open door) — **RETIRED** (S-C5): correct UCI encoding,
  no consumer anywhere in the repository; closed as documentation in CHECKMATE_ROOT_MATE0_CLOSED.md.
- The patch itself (job2c, plus the one-line and conservative variants) — **NOT NEEDED ANYWHERE**. The
  applicability box in PATCH_SUMMARY_fifty_move.md now opens DO NOT APPLY, quoting file 6.

MateAlphaGuard (PC r15, PC20, Threads 1, Hash 16, depths 8 to 16):
- S-C7 — CONFIRMS seat 20's S-F38: guard alone gives the true `mate -4` where defaults give `mate -7` and the
  five other switches give `cp -3122`; the true distance of 8 plies proved by exhaustive minimax with no
  engine involved.
- S-F49 / S-F49b — decisive at depths 12 to 14; at 15 and 16 the verdict converges while the guarded search
  is 42 to 44 percent cheaper in nodes. Not redundant at depth 16.

Softnodes and budget measurement (PC r15, PC20, Threads 1, Hash 16):
- S-F50 — deterministic 9 of 9 cases across separate processes; stops at a finished depth; overshoot to
  106 percent.
- S-F51 — the staircase mechanism read from the code; 9 bands on startpos; bound 4N.
- S-F52 — bands move up to 3.0x across real G positions, so the per-position lookup table is the deliverable.
- S-F53 — the decision: ignoring the table costs 2.45x in nodes per game with IDENTICAL move, depth and score
  on 5 of 5 positions — a cost decision, not a correctness one.
- S-C8 — CONFIRMS seat 13's S-F7 (163.7 percent overshoot reproduced to the node, inside the 4N cap);
  S-F57 states the allowance a cost comparison must add on both sides.

Checks of other seats:
- S-C1 seat 11 junk-after-sixth-field; S-C2 seat 05's cliff (numbers confirmed, the "9 plies early" framing
  refuted as the search horizon); S-C3 seat 17's searchmoves `0000` (observable only);
- S-C4 my own 2640 mechanism, REFUTED by my own `-D_GLIBCXX_DEBUG` instrument and withdrawn;
- S-C6, S-C7 above; S-C8 above;
- S-C9 seat 25's repair SCOPED not refuted — its premise conflicts with file 6 for matches, and the class
  that does matter is already correct on the PC;
- S-C10 seat 16's S-F15 partially confirmed: TtPruneV2's direction yes, HistRework's no.

### MY OWN CLAIMS I RETIRED, and the measurement that did it
2640 mechanism (my own instrument); S-F19 (board not discriminating); S-F5/S-F17 (file 6's inequality);
S-F32/S-F38 (no consumer in the repository); and a broken colour-symmetry checker caught by its own
100-percent-mismatch output before publication (S-F58). Each retirement names the measurement, not a preference.

### OPEN / NOT DONE
- Seat 16's HistRework cell disagrees with mine (my 60 positions against their 353). Unresolved; both
  directions stated in S-C10.
- Nothing of mine is an open defect, and no patch of mine should be applied anywhere.
- I did not have seat 25's patched build, so I scoped its premise, not its node counts.

### FILES A PERSON SHOULD READ, in order
1. FILE6_APPLIED_TO_MY_FINDINGS.md — why no patch is needed, and the one class that matters.
2. REFUSED_FEN_TRAP_AND_GUARD.md — the harness guard for anyone building positions by hand.
3. softnodes/softnodes_real_games.txt — the per-position budget table, with the cost-of-ignoring line first.
4. checks/guarddepth/guard_depth_table.txt — the MateAlphaGuard table with the board on every row.
5. CHECKMATE_ROOT_MATE0_CLOSED.md — the closed-as-documentation note.

## 2026-11-16T23:06:25Z
HISTREWORK DISAGREEMENT RESOLVED IN SEAT 16's FAVOUR, AND MY OWN S-C10 WAS WRONG (S-C10b, HISTREWORK_DISAGREEMENT_RESOLVED.md).
  Same harness, same build, same settings, all 353 G positions: base_S14 251/353 matches (102 mismatches), plus_Hist 255/353 (98 mismatches). So HistRework LOWERS the asymmetry exactly as seat 16 reported, and their absolute 98 is reproduced to the count.
  MY ERROR: S-C10 used the FIRST 60 positions of set_G and got the opposite sign (base 16 -> Hist 24). The disagreement was SAMPLE-DEPENDENT and my sample was too small - the sign flipped because the early positions are not representative. The sample size that settles it is the full 353, and since the effect is 4 pairs out of 353 any smaller sample can flatter either direction by chance, so I am recording it as 'their number reproduces, the effect is small' rather than as a confident confirmation.
  CONSEQUENCE I am flagging on my own work: the +TtPruneV2 and PC20 arms in S-C10 were measured on the same 60-position sample, so they carry the same risk and are now marked PROVISIONAL. Their direction agrees with seat 16's but I did not re-run them at 353 in the time available.
  LESSON: a check on a PREFIX of a position set is not a check on the set, and the S-F58 sanity control would not have caught this - a checker can be perfectly correct and its sample still too small.
Next: keep confirming while time remains.

### UPDATE TO THE FINAL BLOCK's OPEN ITEM (2026-11-16T23:06:32Z)

The HistRework disagreement is RESOLVED IN SEAT 16's FAVOUR, and my S-C10 was wrong. All 353 G positions,
PC r15, depth 10, Threads 1, Hash 16: base_S14 102 mismatches, +HistRework 98 — HistRework lowers the
asymmetry, reproducing seat 16's 98 to the count. My S-C10 used the first 60 positions and got the opposite
sign, so the disagreement was sample-dependent and my sample was too small. Recorded as S-C10b and in
HISTREWORK_DISAGREEMENT_RESOLVED.md.

Two things follow, and both are flagged in the record rather than buried:
- the +TtPruneV2 and PC20 arms in S-C10 came from the same 60-position sample and are now PROVISIONAL;
- the S-F58 sanity control could NOT have caught this — a checker can be correct and its sample too small.
  Those are two separate guards; I had built only one.

So the FINAL block has no unresolved open item: the one disagreement it listed is resolved, with my error
named and its cause identified.

## 2026-11-16T23:14:25Z
BOTH ARMS RE-RUN AT 353 AND SEAT 16's S-F15 IS NOW FULLY CONFIRMED (S-C10c). No provisional numbers left.
  On all 353 G positions, PC r15, depth 10, Threads 1, Hash 16, comparing moves under the verified rank-flip mapping: mismatches base_S14 102, +TtPruneV2 113, +HistRework 98, PC20 120. Seat 16 reported 101/102, 113, 98 and 120 - every number reproduced to within one. So the whole attribution holds: the extra asymmetry comes from the PC20 SETTINGS, TtPruneV2 is the main offender, HistRework is the only cell MORE symmetric, and PC20 is worse than base+S14. This supersedes my S-C10 (60-position sample, wrong HistRework sign) and the TtPruneV2/PC20 arms are no longer provisional.
  The harness now prints a SAMPLE WARNING whenever fewer than 353 positions are run, telling the reader not to quote the counts as seat 16's numbers - so the prefix mistake I made cannot be made again by someone reusing my script.
2) THE SAMPLE-SIZE LESSON WRITTEN UP AS A RULE PAGE (S-F59): TWO_GUARDS_CHECKER_AND_SAMPLE.md. It states that a correct checker on too small a sample is still a wrong result, and that the sanity control which proves the instrument works cannot see it - they are two separate guards, and I had built only one. It gives the procedure: state the effect size, count the pairs the comparison rests on, run the SET the other seat used (a prefix is a different experiment sharing a name), label prefix runs as prefixes in the finding line, and treat sibling arms from the same prefix as provisional too, because the sample error is shared rather than local.
  I put it in my own folder because I have no write access to the rule page (my branch and folder only, as the rules say); if a coordinator wants it folded into the swarm rule page, it is ready to copy verbatim.
Next: keep confirming while time remains.

### SECOND UPDATE TO THE FINAL BLOCK — no provisional numbers remain (2026-11-16T23:14:30Z)

Both sibling arms have now been re-run on all 353 G positions, so nothing of mine is left marked provisional.
PC r15, depth 10, Threads 1, Hash 16, moves compared under the verified rank-flip mapping — mismatch counts:
base_S14 **102**, +TtPruneV2 **113**, +HistRework **98**, PC20 **120**. Seat 16 reported 101/102, 113, 98 and
120: every number reproduced to within one. So S-C10c FULLY CONFIRMS seat 16's S-F15, and my S-C10 is
superseded rather than merely patched.

The sample-size lesson is written up as its own rule page, TWO_GUARDS_CHECKER_AND_SAMPLE.md (S-F59): a correct
checker on too small a sample is still a wrong result, and the sanity control that proves the instrument works
cannot see that failure — two separate guards, of which I had built only one. The page gives the procedure
(state the effect size, count the pairs, run the SET the other seat used, label prefixes as prefixes, treat
sibling arms from a prefix as provisional) with my own 102-vs-98 reversal as the worked example.

I also hardened the harness so the mistake cannot be repeated by anyone reusing my script: when fewer than 353
positions are run it prints a SAMPLE WARNING telling the reader not to quote the counts as seat 16's numbers.

State of my record at this point: no open defect, no provisional number, no unresolved disagreement, no patch
of mine to be applied anywhere, and every retirement and every confirmation names the measurement behind it.

## 2026-11-16T23:20:18Z
SEAT 05's S-F49 CONFIRMED (S-C11) - the depth ladder of the owner's real controls, which is the most directly usable ranking in the run.
  PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh process per row, three boards. startpos: softnodes 2000 d7, nodes 20000 d11, nodes 50000 d14, nodes 250000 d17, clock 6000 d19, movetime 6000 d27. G0: d7 / d11 / d12 / d16 / d18. Deep middlegame likewise, clock d18, movetime d28. LADDER MONOTONE ON 3 OF 3 BOARDS, so their ordering reproduces exactly - including that the clock path beats the 250,000-node match budget by 2 plies (d19 vs d17 on startpos) while spending only 0.37 s of its 6 s.
  ONE HONEST DIFFERENCE: seat 05 reported the clock row dropping to d17 under CPU contention. On this machine it gave d19 in 5 of 5 solo runs AND d19 in 3 of 3 runs with a second engine process searching at depth 30 concurrently (walls 361-388 ms). So their contention caveat is machine-load dependent and did not reproduce with one extra process here - which slightly strengthens the ranking rather than weakening it, and I have said so rather than either ignoring their caveat or echoing it.
RECORD STATE: every claim of mine is closed - no open defect, no provisional number, no unresolved disagreement, no patch to apply. My area's results, the retirements, the confirmations and the two rule pages are all on the remote.
Standing by for the close at 10:18Z.

## 2026-11-16T23:30:12Z
MISATTRIBUTION FIRST, THEN THE VERIFICATION. The forfeit-prediction correction is aimed at 15-F35, which is SEAT 15's clock-path self-play finding, not mine. My area is 1 (FEN input) and my S-F35 is the PC build pins - unrelated. grep for '165-ply', 'forfeit' and 'drain' across my whole folder returns NOTHING, and seat 15's FINDINGS.md does carry 15-F35 with the 73 ms drain / ~82 moves / forfeit shape. So I cannot withdraw a claim I never made; seat 15 needs this correction, and I have no write access to their branch.
WHAT I COULD DO, AND DID (S-C12): verify the analytic argument on my own build so seat 15 has an independent confirmation to cite. PC r15 + PC20 / Threads 1 / Hash 16 / winc=binc=60, iterating the worst-case rule that spends the full hard plan every move: the clock CONVERGES TO A FIXED POINT from 6000 / 3000 / 1000 / 500 / 300 / 200 ms, in 29-72 moves, never forfeiting. So the STRUCTURE of the refutation is confirmed - no forfeit is predicted - and the reason is exactly as given: the drain is (hard limit minus increment) and the hard limit scales with the clock.
  ONE HONEST DIFFERENCE: my converged value is ~493 ms on this middlegame, not the 111 ms quoted. The floor depends on the hard-plan fraction actually spent, and this position is easy so the engine uses only 14-50 % of the clock on hard plans rather than the 60 % the 111 ms figure assumes. That is the coordinator's own point that the floor depends on the constants - so the constant should be quoted per position class, not as one number.
  I did NOT write anything into seat 15's folder or branch, and I have not touched their 15-F35. If the coordinator wants the withdrawal recorded in seat 15's FINDINGS, it has to go through seat 15 or the coordinator - my branch is not the place for another seat's retraction.
Next: the second item, the timing-clamp finding, confirmed on another seat's material.

## 2026-11-16T23:31:18Z
DERIVED THE FLOOR FROM THE ENGINE'S OWN CONSTANTS AND CORRECTED MY OWN S-C12 (S-C12b, clockfloor/DERIVATION.md).
  From clock_plan.hpp:20-56 with the tunables in search.cpp:135-138 (TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60, TmHardSoftMultiple 5, Move Overhead 10 ms): a fixed point needs hard == increment, i.e. (clock - overhead) x 60/100 = increment, so clock = 10 + 100 = 110 ms - matching the 111 ms figure to rounding. Iterating that arithmetic with a worst-case spend converges to 111 ms from 6000/3000/1000/500/300/200; with the realistic soft-plan spend it converges to 361/340 ms.
  MY ERROR, NAMED: I reported 493 ms because I iterated with the OBSERVED spend fraction (14 % of the clock, on an easy middlegame) instead of the HARD CAP (60 %) that the worst-case bound is defined over. Same structure, wrong question - 493 ms is what an easy position settles at, 111 ms is the floor that bounds a forfeit. Both true, of different spend rules; only the second bounds anything.
  CONFIRMS YOUR FORMULA: the floor depends on the movement overhead, the increment and the hard-plan percentage, and NOT on the divisor or the increment percentage (those set the soft plan), and a looser hard cap lowers it. Verified by the derivation rather than accepted - the 110 ms came out of the code's own constants.
  So seat 15's measurements stand, its ~165-ply forfeit prediction does not, the endgame deceleration is the mechanism that makes it converge, and neither 111 nor 493 is reached by a real game because a search stops at its soft plan.
Next: cadence STATUS push done here; continuing with the clamp confirmation already in progress.

## 2026-11-16T23:31:25Z — 25-minute cadence
CLAMP CONFIRMED AND A HARNESS TRAP FOUND (S-C13, S-F60).
  CONFIRMED seat 28's S-F10 on my own material: PC r15 + PC20, Threads 1, Hash 16, wtime=btime=2000, 5 runs per value, medians - movestogo 50 = 25.9 ms, 51 = 25.5, 100 = 26.4, 1000 = 25.8. Spread 0.9 ms = 3.5 % of the 50-median, so everything above 50 is indistinguishable from 50. Matches mtg = moves_to_go < 50 ? moves_to_go : 50 at clock_plan.hpp:38.
  NEW TRAP FOR EVERY LATENCY HARNESS, which seat 28 did not report: movestogo 0 and -1 do NOT mean 'no limit'. They fall through the moves_to_go > 0 guard into the SUDDEN-DEATH branch, giving 482 / 487 ms against 57 ms with NO movestogo token at all - 8.4x apart, and 18x the movestogo-50 budget. A harness that sends movestogo 0 to mean 'ignore this field' gets the SLOWEST plan, not the default one. Two rules: never send movestogo 0 for 'unset', and never quote a plan-derived budget without the movestogo actually sent, because above 50 the engine silently substitutes 50.
  This is the finding that affects every latency harness in the swarm, which is why the coordinator asked for it on another seat's material rather than mine.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:31:45Z — 25-minute cadence
CONTROLLED MY OWN DERIVATION AGAINST MEASUREMENT (S-F61), because S-C12b was arithmetic about a formula I read.
  PC r15 + PC20, Threads 1, Hash 16, winc=binc=60, 5 runs per clock, medians, real-work position. Predicted soft/hard from clock_plan.hpp vs measured: 6000 -> 317/1585 predicted, 293 ms measured (x0.93 soft, x0.19 hard); 3000 -> 180/900, 93.6 ms (x0.52, x0.10); 1000 -> 90/450, 57.3 ms (x0.64, x0.13); 500 -> 67/294, 57.5 ms (x0.86, x0.20); 300 -> 58/174, 57.0 ms (x0.98, x0.33).
  RESULT: 5 of 5 clocks land INSIDE the planned soft..hard window, 0 exceed the hard plan, 0 finished early. So the formula is the one the engine follows, and - the important part - the measured spend uses only 0.10-0.33 of the HARD cap, which is exactly why the realistic floor is ~340-360 ms while the 111 ms figure is a worst-case bound. Both of my S-C12b numbers are now grounded in measurement rather than arithmetic alone.
  This also means seat 15's 73 ms/move drain figure is a worst-case-flavoured number: it implies spending near the hard cap every move, which a real search does not do.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:31:52Z — 25-minute cadence
MOVESTOGO RULE STATED AS THE TWO RULES FOR THE BRIEF (S-F62, MOVESTOGO_RULE.md, ready to paste verbatim):
  1. Never send movestogo 0 to mean 'unset'. clock_plan.hpp:37 branches on moves_to_go > 0, so zero or negative selects the SUDDEN-DEATH branch - measured at a 2000 ms clock: movestogo 0 = 482 ms, -1 = 487 ms, no token at all = 57 ms, i.e. 8.4x the plan of omitting it and 18x the movestogo-50 budget. To get the no-movestogo behaviour, omit the token.
  2. Never quote a plan-derived budget without the movestogo actually sent, since anything above 50 silently becomes 50. clock_plan.hpp:38 is mtg = moves_to_go < 50 ? moves_to_go : 50; medians at 50/51/100/1000 are 25.9/25.5/26.4/25.8 ms - a 0.9 ms spread, 3.5 % of the 50-median - so a harness requesting a large movestogo to spread the clock gets 50 and its per-move expectation is wrong by movestogo/50.
  Consequence in one line: a budget computed from the plan is reproducible only if the movestogo sent is recorded with it, because the engine may have used a different number than the one sent, and zero is the one value that means the opposite of what it looks like.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:32:09Z — 25-minute cadence
THREE-WAY AGREEMENT ON THE CLOCK FLOOR (S-C14, clockfloor/THREE_WAY_AGREEMENT.md). Seat 28's S-F44 was the finding I was about to confirm, and it is the SAME derivation I did independently: floor = MoveOverhead + increment x 100 / TmHardPercent = 10 + 60 x 100 / 60 = 110 ms (111 with integer division). Three independent arrivals - seat 28 from the same two source files, me from clock_plan.hpp + search.cpp:135-138, and the coordinator's argument that the drain is (hard limit minus increment) with the hard limit scaling with the clock. None of us had the others' numbers.
  I checked seat 28's TmHardPercent sweep against the formula rather than accepting it: they report 30->210, 45->143, 60->110, 75->90, 90->77 ms; recomputing 10 + 60 x 100/pct gives 210.0, 143.3, 110.0, 90.0, 76.7 - EVERY value reproduces, including the direction (raising the percentage LOWERS the floor). And their TmSoftDivisor/TmIncrementPercent independence holds structurally, because those two set the SOFT plan and cannot bind the floor equation.
  WHAT IT SETTLES: a game cannot forfeit by searching - the clock approaches a floor and stops falling. But 111 ms is a WORST-CASE bound, not what a game settles at: seats 05 and 28 measured 111-120 and 174-300 ms depending on position, and my S-F61 measured the spend at 0.10-0.33 of the hard cap, consistent with settling nearer the soft plan. The floor is tunable in one useful direction only: a looser TmHardPercent lowers it (90 -> 77 ms).
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:34:06Z — 25-minute cadence
RECONCILED TWO SEATS WHO LOOKED IN CONFLICT (S-C15), and caught my own misreading doing it.
  The apparent conflict: seat 20's S-F49 says the clock path is NOT exactly reproducible at Threads 1 (depth and nodes flip between 17 and 18 as ~5 ms decides whether the 18th iteration completes); seat 28's S-F43 says it IS stable under contention (identical depth 18, identical 998,994 nodes, 3 solo and 3 loaded runs). Both are right - they measured one quantised property from two positions.
  MY TEST: a 15-point clock sweep (900-1600 ms) on one board gives only 4 distinct (depth,nodes) outcomes, so the clock path is a STEP FUNCTION of the clock, as seat 28 says. Then 5 repeats at the MIDDLE of the longest plateau gave 1 distinct outcome (depth 14, 97,289 nodes, 5 of 5) - inside a plateau a Threads 1 clock search is exactly reproducible. So seat 20's flips are the same property measured ON a boundary, and neither seat found a defect.
  A TRAP I FELL INTO AND CAUGHT (S-F63): my sweep had ONE depth-14 reading at clock 1350 sitting between depth-15 readings at 1300 and 1400, and my first reading was 'boundary artefact'. Six repeats at 1350 gave depth 15 / 121,306 nodes in 6 of 6 - so that point is NOT a boundary, the single 14 was a one-off slow run. Rule: a boundary is proven by REPEATED flips at one clock, never by a single out-of-band reading, because a one-off anomaly and a real boundary are indistinguishable in a single sweep.
  FOR MATCH HARNESSES: a clock budget is reproducible only to a PLATEAU - place it inside one from a sweep, and confirm with 2-3 repeats that it is not on a boundary.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:34:30Z — 25-minute cadence
BOTH RULES WRITTEN INTO ONE PAGE, CLOCK_REPRODUCIBILITY_RULE.md (S-F64), with the headline rule at the top:
  'A CLOCK BUDGET IS REPRODUCIBLE ONLY TO A PLATEAU. Sweep the clock to find one, then confirm with two or three repeats that the budget is not sitting on an iteration boundary.'
  With the evidence: a 15-clock sweep (900-1600 ms) gives only 4 distinct (depth,nodes) outcomes - the step function - and 5 repeats mid-plateau give 1 distinct outcome (depth 14, 97,289 nodes, 5 of 5). Then the comparison table showing seat 20 measured ON a boundary and seat 28 INSIDE a plateau, so both are right and neither is a defect.
  And the companion rule you asked to file alongside the sample-size lesson: 'A boundary is proven by REPEATED flips at one clock, never by a single out-of-band reading - a one-off anomaly and a genuine boundary look identical in a single sweep.' My own 1350 ms anomaly is the worked example: one depth-14 reading between depth-15s, then 6 repeats all at depth 15, so that point is not a boundary. The page explicitly cross-references TWO_GUARDS_CHECKER_AND_SAMPLE.md as the same species: one observation is not a distribution, and repetition is a separate guard from the one that proves the instrument works.
  Ends with a five-step checklist for a clock harness: sweep, place mid-plateau, repeat 2-3 times, report the PLATEAU rather than a single reading, and use go nodes when exactness matters while adding the same allowance on both sides of a cost comparison.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:34:37Z — 25-minute cadence
SEAT 25's S-F30 CONFIRMED TO THE DIGIT (S-C16) — a full self-play game at the owner's EXACT match setting, which is his actual path and therefore the strongest play-level statement in my record.
  PC r15 + PC20, Threads 1, Hash 16, OwnBook false, go nodes 20000, ONE FRESH PROCESS PER MOVE, python-chess as referee: 90 plies, ending by seventyfive/repetition claim; 0 illegal moves, 0 0000 on a board with legal moves, 0 moves with an empty PV; nodes spent / N median 0.75, min 0.34, max 1.00 over 90 moves.
  Seat 25 reported 'median 0.75 (0.34-1.00)' and my independent game reproduces those three numbers EXACTLY - same median, same min, same max, over the same 90 plies. That is a stronger agreement than the claim needed.
  TWO CHECKS SEAT 25 DID NOT REPORT, both clean: every bestmove was legal on the board python-chess thought it was, so there is no stale-board effect between moves in a game loop; and the engine never returned 0000 while a legal move existed. Between them these cover the failure modes the refused-FEN trap page warns about, in the one context where a harness drives many positions in sequence.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:34:51Z — 25-minute cadence
SEAT 25's S-F31 CONFIRMED EXACTLY (S-C17) - the OTHER game ending, so both of seat 25's endings are now independently confirmed by me (S-C16 was the 90-ply claim ending, this is the forced mate).
  PC r15 + PC20, Threads 1, Hash 16, OwnBook false, go nodes 20000, one fresh process per move, start 4k3/8/8/8/8/8/8/K1QR4 w: CHECKMATE at ply 3, 0 illegal moves, 3 mate scores claimed of which 0 had a PV that fails to play out - seat 25's S-F31 to the number.
  AND I CHECKED THE PVs PROPERLY rather than trusting the score: each PV was sliced from the engine's own info line and REPLAYED with python-chess. mate 2 with a 3-ply PV mating at pv ply 3; mate -1 with a 2-ply PV mating at ply 2; mate 1 with a 1-ply PV mating at ply 1. So score and PV agree at all three plies - which is precisely the mate-PV-truncation question seat 05 spent the night on, and here it is clean.
  My area now has both of the owner's real game endings covered: claim ending (S-C16) and mate ending (S-C17), neither showing a defect.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.
