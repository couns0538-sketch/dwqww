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

### THIRD UPDATE TO THE FINAL BLOCK — the owner's real game paths are clean

Since the FINAL block was written I confirmed both of the owner's actual game endings at his exact match
setting (PC r15 + PC20, Threads 1, Hash 16, OwnBook false, `go nodes 20000`, one fresh process per move):

- **claim ending** (S-C16): 90 plies ending by seventyfive/repetition; **0 illegal moves, 0 `0000` on a
  playable board, 0 moves with an empty PV**; nodes spent / N **median 0.75, min 0.34, max 1.00** — seat 25's
  reported band reproduced to the digit.
- **mate ending** (S-C17): **checkmate at ply 3**, 0 illegal, **3 mate scores of which 0 had a PV that fails
  to play out** — each PV sliced from the engine's `info` line and replayed with python-chess; score and PV
  agree at all three plies.

These are the strongest play-level statements in my record because a match is what they test: many positions
driven in sequence through one board, the context where a refused position or a stale board would surface as
an illegal move. Neither showed a defect.

### ALSO ADDED SINCE THE FINAL BLOCK

- **S-C12b / S-C14** — the clock floor derived from the engine's own constants:
  `MoveOverhead + increment*100/TmHardPercent` = **110 ms** (111 with integer division), reached
  independently by seat 28's S-F44 and by the coordinator's argument. My earlier S-C12 figure of 493 ms is
  corrected: it iterated with the observed spend (14 percent of clock) rather than the hard cap (60 percent)
  the bound is defined over.
- **S-F61** — control on that derivation: on five clocks, predicted soft/hard vs measured spend gave **5 of 5
  inside the planned window, 0 over the hard cap**, with the spend at **0.10-0.33 of hard** — which is why the
  realistic floor is ~340-360 ms while 111 ms bounds a forfeit.
- **S-F62 / MOVESTOGO_RULE.md** — the two rules for every latency harness: never send `movestogo 0` to mean
  unset (it selects sudden-death and is 8.4x slower than omitting the token), and never quote a plan-derived
  budget without the movestogo actually sent (anything above 50 silently becomes 50).
- **S-C15 / S-F64 / CLOCK_REPRODUCIBILITY_RULE.md** — seats 20 and 28 reconciled: the clock path is quantised
  and reproducible only to a plateau; and a boundary is proven by repeated flips, not one out-of-band reading.

### THE TWO CHECKS THAT PROVE A LONG SEQUENTIAL LOOP IS SAFE

These were additions of mine to seat 25's S-F30, and they belong in the FINAL as their own lines, because a
game is not one position tested safely — it is ninety positions driven through one board in sequence, which is
the only context where a stale board or a refused position can compound.

- **S-C16 check A — every bestmove legal on the board python-chess believes it is.** 90 of 90 moves legal. A
  harness that lost track of the position between moves would show up here as an illegal move; the engine's
  bestmove was checked against the referee's board, not against its own belief about it. This is the check that
  makes the refused-FEN hazard (REFUSED_FEN_TRAP_AND_GUARD.md) testable in the one context a match runs in.
- **S-C16 check B — never `0000` while a legal move exists.** 0 occurrences in 90 plies. `0000` is UCI for
  "no legal move"; an engine that answered it on a playable board would hand a GUI an illegal move, which is
  the failure seat 17 found via `searchmoves` and which this check rules out for the ordinary game path.

Together they turn "the engine plays a position correctly" into "the engine plays a sequence correctly", which
is the statement a match actually needs. Both clean at the owner's exact match setting.

### ONE MORE HARNESS LESSON, self-caught

A `%`-formatted STATUS write crashed on literal percent signs in the text and silently dropped a block; and a
misdirected `cd` left a stray `STATUS.md` in the repository root (untracked, so never in history; removed).
Both are the same class as the refused-FEN trap: a mechanical step that fails quietly. The guard is the same —
after writing, read back what was written and check `git status` for anything outside your own folder.

## 2026-11-16T23:40:33Z — 25-minute cadence
SEAT 25's S-F7 CONFIRMED AND EXTENDED (S-C18, S-F65). A terminal root emits 64 info lines at 0 nodes - confirmed on BOTH terminal types, with the control that makes it a finding rather than a loop defect.
  Checkmated root 4R1k1/5ppp/8/8/8/8/5PPP/6K1 b: go depth 5 -> 5 lines; go nodes 100, go movetime 50 and go depth 64 -> 64 lines each, max depth 64, nodes 0, bestmove 0000. Stalemated root 7k/5Q2/8/8/8/8/8/K7 b: identical. Seat 25 reported one terminal case; I confirm both endings and add go depth 64 to the affected commands.
  THE CONTROL that makes this a finding: a NORMAL root gives 1 line for go nodes 100 (max depth 1, 67 nodes) and 13 for go movetime 50. So the phantom iterations are TERMINAL-SPECIFIC, not a general loop defect - which is exactly the scoping seat 25 asked for.
  MECHANISM FROM THE CODE (S-F65): the iterative-deepening loop emits one info line per iteration and leaves only on a break; on a terminal root nothing increments the node count, so should_stop() is never true and the loop runs to max_depth emitting an empty line each time. Harmless for strength, but a depth-keyed training label or progress bar reads 64 iterations of progress on 0 nodes of work, and a latency harness timing a terminal position is timing an empty loop.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### ONE MORE DOOR, now with a confirmed scope: the terminal root

S-C18 / S-F65 confirm seat 25's S-F7 and fix its scope. On a **terminal** root (checkmated OR stalemated),
`go nodes 100`, `go movetime 50` and `go depth 64` each emit **64 `info depth` lines at 0 nodes**, while
`go depth 5` correctly emits 5. A **normal** root emits 1 line for `go nodes 100`. So it is terminal-specific:
the iterative-deepening loop leaves only on a `break`, and a terminal root does no work, so nothing trips the
stop condition and the loop runs to the 64-depth cap.

Why it is in the FINAL despite being cosmetic: it is the one remaining defect my area can see on the PC build,
and it is a **harness hazard rather than a strength hazard** — a depth-keyed training label reads 64 iterations
of progress on 0 nodes, a progress display shows a search that never happened, and a latency harness timing a
terminal position times an empty loop. It is not the fifty-move family and it is not `mate 0`; it survives on
the r15 tree.

**State of my area, one line:** no defect that affects play; both of the owner's game endings confirmed clean at
his match setting; one cosmetic harness hazard on terminal roots, scoped and explained; no patch of mine to be
applied anywhere.

## 2026-11-16T23:42:24Z — 25-minute cadence
SEAT 13's S-F18 CONFIRMED (S-C19) — and it changes what the owner should be told he runs.
  (A) Read the switch defaults FROM THE SOURCE THAT PRODUCED MY PC BINARY, not from the patch text: FORGE_FIX_ROOT_DRAWN 1 (search.cpp:36), ISREADY_PENDING 1 (uci.cpp:38), HARD_LIMIT_EMERGENCY 1 (search.cpp:43), BARE_KING_LMR_CAP 1 (search.cpp:63), GO_PARSE 1 (uci.cpp:31) - and BARE_KING_ONE_THREAD 0 (search.cpp:55) and ABORT_PUBLISH 0 (search.cpp:77). So 2 of 7 default to 0, exactly as seat 13 reported.
  (B) The GO_PARSE behavioural signature reproduces with a working control: malformed 'go wtime btime 50' gives PC 3 lines / depth 3 / 215 nodes vs base 1 line / depth 1 / 26 nodes (DIFFERS), while the well-formed 'go wtime 50 btime 50' is IDENTICAL on both builds (4 lines, depth 4, 404 nodes). So the difference is attributable to the parse fix rather than to build drift.
  THE POINT FOR THE OWNER (S-F66): what he runs is FIVE of the patch's seven fixes, not seven. The two that are off are off for measured reasons recorded in the patch itself, and the gentler BARE_KING_LMR_CAP replaces the first - but a reader who credits the PC build with 'seven fixes' credits it with two it does not have.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### THE PC TREE'S REAL FIX COUNT — five of seven, verified on the source I built

S-C19 / S-F66. Read from the source that produced my own PC binary, not from the patch text:

| switch | default | location |
|---|---|---|
| `FORGE_FIX_ROOT_DRAWN` | **1** | `search.cpp:36` |
| `FORGE_FIX_ISREADY_PENDING` | **1** | `uci.cpp:38` |
| `FORGE_FIX_HARD_LIMIT_EMERGENCY` | **1** | `search.cpp:43` |
| `FORGE_FIX_BARE_KING_LMR_CAP` | **1** | `search.cpp:63` |
| `FORGE_FIX_GO_PARSE` | **1** | `uci.cpp:31` |
| `FORGE_FIX_BARE_KING_ONE_THREAD` | **0** | `search.cpp:55` |
| `FORGE_FIX_ABORT_PUBLISH` | **0** | `search.cpp:77` |

Each off for a measured reason recorded in the patch itself, and `BARE_KING_LMR_CAP` (on) replaces the first.
But **"the PC patch's seven fixes" is five in the binary the owner plays**, and that is worth saying wherever
the r15 tree is described.

The one behavioural half of that finding which needed a second seat: `GO_PARSE` reproduces **with a working
control** — malformed `go wtime btime 50` gives PC 3 lines / depth 3 / 215 nodes against base 1 line / depth 1
/ 26 nodes (differs), while the well-formed `go wtime 50 btime 50` is identical on both builds (4 lines,
depth 4, 404 nodes). So the difference is the parse fix, not build drift.

## 2026-11-16T23:42:37Z — 25-minute cadence
WROTE THE TERMINAL-ROOT MECHANISM UP AS ITS OWN PAGE (S-F67, TERMINAL_ROOT_MECHANISM.md), keeping the mechanism you asked to retain: the iterative-deepening loop leaves on the soft-node stop or on should_stop(); a terminal root does no work, so the node count never rises, neither test can fire, and the depth cap becomes the loop's ONLY exit - which is why it emits 64 empty lines rather than looping forever.
  The page carries the command table (go depth 5 = 5 lines correct; go nodes 100, go movetime 50 and go depth 64 = 64 lines at 0 nodes on terminal roots; normal root go nodes 100 = 1 line), the mechanism, why the normal-root control is what makes it a finding rather than a loop defect, and a per-consumer cost table: a depth-keyed training label records 'depth 64' for a position where nothing was searched, a progress display shows a search that never ran, a latency harness times an empty loop, a PV checker sees 64 empty PVs, and strength is unaffected because bestmove 0000 is right.
  Rule at the end: special-case a terminal root before measuring anything from it, because a well-formed 64-line answer to a finished game is entirely artefact.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:44:31Z — 25-minute cadence
SEAT 02's S-F13 CHECKED (S-C20) - part A confirmed MORE strongly than their own figure, part B not demonstrated, and I say which is which.
  (A) CONFIRMED: PC r15 + PC20, Threads 1, Hash 16, go wtime 6000 btime 6000 winc 60 binc 60, one fresh process per board, first 16 of set_G. Spearman rho(wall time, the last completed iteration's OWN reported time) = 1.000 over 16 boards, and 16 of 16 have wall within 10 % of that iteration's time (typical difference 0.5-1.1 ms). So a clock move's wall time IS the last completed iteration's cost - seat 02 concluded exactly this at rho 0.998, and my sample gives 1.000.
  (B) NOT DEMONSTRATED: 0 of 16 boards showed wall much greater than the last iteration, i.e. no hard-limit cut. That is CONSISTENT with seat 02's 'the hard limit is the only route to an expensive move' because the cut is rare and a 16-board set_G sample may miss it - but it does not reproduce the phenomenon, and I have recorded it as not demonstrated rather than implying a confirmation I did not get.
  WHY IT MATTERS (S-F68): a clock move costs its last completed iteration, so go wtime W is NOT a fixed fraction of W - the cost varied 285-800 ms across 16 ordinary positions at the SAME 6 s clock. That is precisely why a clock-derived budget is not reproducible while a node budget is: wall time is a step function of iteration cost, not of the clock.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:47:24Z — 25-minute cadence
REPLIED TO SEAT 27 WITH THE NUMBERS IT ASKED FOR, AND FIXED AN ATTRIBUTION (S-F69, S-F70, clocknodes/REPLY_TO_SEAT_27.md).
  THE NUMBERS: median NODES per move 263,746 (mean 335,871, min 16,294, max 961,458, n=144); median wall 129.2 ms; median net drain 69.2 ms against the 60 ms increment; PLY CAP USED 400 (the game ended at 144); final clocks 2,996 / 2,703 ms; NO FORFEIT. PC r15 + PC20, Threads 1, Hash 16, one fresh process per move.
  THE ATTRIBUTION CORRECTION THAT MATTERS: the '105 ms median drain' and the '~165-ply forfeit prediction' that seat 27 is reconciling against are SEAT 15's (15-F35), not mine. My clock work is the fixed point (S-C12b/S-C14), the cost model (S-C20/S-F68, rho 1.000) and the quantisation rule (S-C15/S-F64). I have never published a 105 ms drain. Two seats were chasing a gap that is mostly between 105 and ~80 ms, and 105 is not my number.
  AGAINST MY ACTUAL 69.2 ms, seat 27's 78.6-81.7 ms is within 15% - so no machine-speed explanation is needed for that part at all.
  ITS THREE CANDIDATES ANSWERED: (1) machine speed largely ruled out - my machine is the same class (4 vCPU Xeon virtualised, AVX-512F + BMI2, g++ 13.3, load 0.14-0.32); (2) the wall-clock measurement point is the most likely remaining difference, and if it subtracts Move Overhead (10 ms) that alone explains most of the residual gap; (3) the ply cap cannot explain a per-move median directly, but a longer cap shifts the position mix and my later moves cost more (max 534 ms against a 129 ms median) - I used 400 and the game ended at 144.
  Also returned its forfeit correction: thank you, but that is seat 15's prediction it has now supported, not mine, and I should not be credited with it. My 144-ply game had no forfeit, which is consistent with the fixed point decelerating the drain.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:47:33Z — 25-minute cadence
SAMPLE NOTE RECORDED BESIDE S-C20's NEGATIVE (S-C20b), as you asked: '0 of 16 boards showed the hard-limit cut' is a statement about a 16-board SAMPLE, not evidence the cut cannot happen. Sixteen ordinary game positions can miss a rare pathological shape - seat 02 found the cut on a SPARSE ENDGAME WITH 5 LEGAL MOVES, which the first 16 of set_G need not contain. So part (B) is NOT DEMONSTRATED at n=16, not refuted, and the sample size now sits in the finding line and in the output file itself, so anyone quoting the zero quotes its n with it.
  That is the third place tonight the same discipline has earned its keep: the 60-position symmetry sample that gave me the wrong sign, the single 1350 ms anomaly that was not a boundary, and now this negative at n=16. In each case the number was true and the claim around it was not.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:47:44Z — 25-minute cadence
WROTE THE ATTRIBUTION RULE UP AS A SWARM-LEVEL PAGE, ready to paste into the brief (S-F71, ATTRIBUTION_RULE.md).
  THE RULE: 'Before you reconcile against another seat's number, confirm that seat actually published it.' A number quoted second-hand carries the name of whoever repeated it, not whoever measured it.
  WHY IT IS A DIFFERENT ERROR FROM A WRONG NUMBER, which is the part worth keeping: a wrong number can be caught by re-measuring; a MIS-ATTRIBUTED one cannot, because the owning seat cannot defend or correct it and the reconciling seat cannot find the method behind it - it is looking in the wrong record. The time goes on a gap that is an artefact of the labelling. And it is self-reinforcing: once repeated with a name, the next summary repeats it with that name and the original becomes hard to find.
  THE CHECK, which costs one search: open the seat's FINDINGS.md and look for the number; if it is there under a different finding id, quote the id you found; if it is nowhere, treat it as unattributed and say so; and whenever you quote, name the seat AND the finding id AND the build and settings, because a number without those is not checkable.
  Plus the corollary for the seat being quoted: if a figure circulates with your name on it that you did not publish, say so plainly and give the figure you did measure - cheaper for everyone than letting a nearby-but-different number stand, and not a criticism of whoever repeated it, because the labelling error is usually nobody's.
  Seat 27's measurement-point question is with the coordinator (does it subtract Move Overhead) - recorded in my reply as the most likely residual and the one that flips sign.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:48:05Z — 25-minute cadence
SEAT 02's S-F9 AND S-F10 CONFIRMED (S-C21), and they complete a family worth one page in the brief (S-F72, MEASUREMENT_TRAPS.md).
  DILUTION CONFIRMED on all three budget types on my own board: go nodes 20000 d10 at MultiPV 1 -> d7 at MultiPV 8 (loss 3); go nodes 50000 d12 -> d8 (loss 4); go softnodes 2000 d8 -> d2 (loss 6, the worst). SUBLINEAR as seat 02's S-F10 says: on 20,000 nodes MultiPV 1 -> d10, 4 -> d8, 8 -> d7. And the truncation is real: 5 of 9 MultiPV>1 cells report FEWER lines at the deepest depth than the setting, so a GUI reading all M lines gets stale ones.
  THE PAGE: MEASUREMENT_TRAPS.md gathers the three settings that silently change what a harness measures - MultiPV above 1 divides a node budget, movestogo 0 selects sudden-death (8.4x the plan of omitting it), and Threads above 1 varies run to run by design. Headline: 'Assert and record Threads 1, MultiPV 1, and never send movestogo 0.'
  THE COMMON SHAPE, which is why they belong together: all three are settings whose NAME suggests they do not matter to the measurement. So assert them explicitly, record them in the OUTPUT rather than only in the script, and when a number looks wrong check the settings BEFORE the engine - two of tonight's three were a setting, not a search defect. Same family as the attribution rule: the failure is never in the number and it is never announced.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:48:23Z — 25-minute cadence
ATTRIBUTION RESOLVED (S-F73), and seat 27 IS FACTUALLY RIGHT: I checked seat 15's FINDINGS.md and 'median 105 ms used' plus the ~165-ply forfeit prediction ARE literally in 15-F35. So my S-F70 needs the reading 'not mine', not 'nobody published it' - both statements are true together, and S-F73 now says so in one sentence so a reader of 15-F35 is not left with two contradictory claims.
  AND THE STORY IS NOW COMPLETE, which is better than either of us had: seat 15 has RETRACTED the prediction in its own 15-R4. It withdrew the constant-cost assumption, kept the distribution (median 104 / p90 269 / p95 368 / p99 564 ms, 80.3% of moves above the increment) and the 0-forfeits-in-36 result, and derived the SAME fixed point I did - its C* = (increment + MoveOverhead)/(TmHardPercent/100) = 116.7 ms against my MoveOverhead + increment*100/TmHardPercent = 110 ms, the two differing only in whether the overhead enters before or after the division.
  So: the 105 ms was real, was seat 15's, and its forfeit conclusion has been withdrawn BY SEAT 15. Seat 27's ply-106 forfeit is its own reproduction of a prediction its author has since retracted - not evidence for anything, and it is right not to credit me with it.
  Seat 27's Move Overhead correction accepted: it does not subtract the 10 ms default, so its corrected figures are 68.6 and 71.7 ms against my 69.2 ms - within 4%, and it withdraws the machine-speed candidate entirely.
Next: run seat 27's process policy (one reused process per game, warm) and report my median under it, which closes the last open number.

## 2026-11-16T23:51:06Z — 25-minute cadence
PROCESS-POLICY EXCHANGE RUN — and it answers seat 27's separator cleanly (S-C22, policyexchange/EXCHANGE_RESULT.md).
  COLD (one fresh process per move, my S-F69): median 263,746 nodes/move, mean 335,871, n=144. WARM (one reused process per game, SEAT 27'S POLICY): median 285,683, mean 364,524, n=80. So adopting its policy moved my median by +8.3 PERCENT, in the direction of MORE nodes - while its figure is 45 PERCENT BELOW my cold number. Warmth cannot explain a 45% shortfall when adopting the warm policy RAISES the figure. SEPARATOR ANSWER: it is POSITION MIX.
  The visible mix differences: (a) ply cap - it capped at 200, my cold game ended at 144 and warm at 80, and my per-move cost RISES through a game (max 534 ms cold / 1,006 ms warm against medians 129 / 157), so a 200-ply game is weighted differently; (b) opening repetition - its 671 moves were drawn from my four opening FENs, so a large share are early moves of similar positions, and early moves are cheaper, pulling a median down.
  RESIDUAL, HONESTLY: 285,683 vs its ~145,000 is a factor of ~2 that neither of my two policies explains. My policies bracket 263k-286k and its figure sits below both. Closing it fully needs the same positions played under both policies, which neither of us has run.
  ONE SURPRISE WORTH KEEPING (S-F74): the WARM policy is SLOWER per move, 156.9 ms against 129.2 ms cold - the opposite of the usual warm-is-cheap assumption. The warm process reaches greater depths (max 1,645,645 nodes vs 961,458), so at a 6 s clock the extra depth costs more than the reused hash saves. For a match, the per-move cost is the WARM one and it is HIGHER than a cold benchmark predicts.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### FOURTH UPDATE — the process-policy exchange, and a cost-model correction

Run at seat 27's request, PC r15 + PC20 / Threads 1 / Hash 16 / 6 s + 0.06:

| policy | median nodes/move | mean | n | median wall |
|---|---|---|---|---|
| cold — one fresh process per move (S-F69) | **263,746** | 335,871 | 144 | 129.2 ms |
| **warm — one reused process per game (seat 27's)** | **285,683** | 364,524 | 80 | **156.9 ms** |

**Two results, one of them unexpected:**

1. **Table warmth is NOT the explanation for its 45 % lower figure.** Adopting its policy moved my median
   **+8.3 %**, in the direction of *more* nodes, while its number sits 45 % *below* mine. The separator it
   proposed therefore answers **position mix** — its 671 moves came from four opening FENs with a 200-ply cap,
   and my per-move cost rises through a game.
2. **The warm policy is SLOWER per move, not faster (S-F74).** 156.9 ms against 129.2 ms cold — the opposite of
   the usual assumption, because the warm process reaches greater depths (max 1.6 M nodes vs 961 k) and at a
   6 s clock that extra depth costs more wall time than the reused hash saves. **For a match, the per-move cost
   is the WARM one, and it is higher than a cold benchmark predicts.**

Residual, stated plainly: 285,683 against its ~145,000 is a factor of ~2 that neither of my policies explains.
Mine bracket 263k–286k; its figure sits below both.

### ATTRIBUTION, FINAL FORM (S-F73)

"median 105 ms used" and the ~165-ply forfeit prediction **are** in seat 15's `15-F35` — verified verbatim — so
seat 27's point is correct and my S-F70 reads as **"not mine"**, not "nobody published it". **Seat 15 has since
retracted the prediction in its own `15-R4`**, keeping the distribution and the 0-forfeits result and deriving
the same fixed point (its 116.7 ms against my 110 ms, differing only in where the overhead enters). No
contradiction remains for a reader of 15-F35.

## 2026-11-16T23:53:32Z — 25-minute cadence
I HAVE TO CORRECT MY OWN S-F74, and it is the same class of error as the others (S-F74b, S-F75).
  S-F74 said the warm policy is slower per move (156.9 vs 129.2 ms). That compared a WARM 80-PLY GAME against a COLD 144-PLY GAME - so it mixed process policy with position mix, which is precisely the confound seat 27 and I were trying to separate.
  THE CONTROLLED TEST holds the positions and their order FIXED and varies only the policy: clock 6000 -> warm x0.88 wall (194.0 vs 219.9 ms), depth x1.06; clock 2000 -> x1.13 (87.8 vs 77.5), x1.07; clock 1000 -> x1.02; clock 300 -> x1.05. So the wall ratio swings 0.88 to 1.13 - EITHER DIRECTION, within about 13% - while DEPTH is consistently a fraction better warm (x0.96-1.07).
  HONEST STATEMENT: process policy changes per-move wall time by about +-10% with NO STABLE SIGN, and warm is usually slightly DEEPER. My 'warm is slower' claim is WITHDRAWN. What survives from S-F74 is only that the policy should be STATED, not a direction.
  THE METHOD LESSON (S-F75), the fourth of its kind tonight: I changed policy AND changed the sample, then credited the difference to policy. 'I changed X and the number moved' is not evidence when the sample also changed. Same family as S-C10's 60-position sample and S-F63's single anomaly - the number was real in each case and the CAUSAL reading was wrong.
  This also means seat 27's process-policy separator is now cleanly answered by the EXCHANGE's other half: warmth moved my median +8.3% on the same positions, which is the controlled result and stands.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:53:40Z — 25-minute cadence
THE CROSS-SEAT NUMBER IS CLOSED, and both figures now agree (S-C23, S-C24).
  NODES AGREE: with BOTH policies on the SAME four start FENs, seat 27's arms land at 190-262k (warm 190,877/197,987/261,829/192,465; cold 245,809/210,961/256,991/212,022) - i.e. at my 263,746. Its original 145,432 was a SAMPLING ARTEFACT: four games to a 200-ply cap, two of four capped, per-game medians 101,572/145,890/150,497/205,472 - long endgame-heavy games drag the median down. So my node figures agree once the game mixture is matched.
  WALL AGREES once Move Overhead is deducted: its 78.6/81.7 become 68.6/71.7 against my 69.2, within 4%.
  WARMTH IS REAL BUT SMALL: about -9% median nodes on matched positions. That is consistent with my own controlled test (S-F74b: +-13%, no stable sign in wall) and cannot explain a 45% gap - so the gap was position/game mixture, which is exactly what my exchange predicted and what its capping explains.
  THE FORFEIT (S-C24) reproduces in BOTH policies on start 2 rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b at 144-178 plies, so it is a property of THAT OPENING at this control, not of warm-vs-cold policy. Worth stating because 'process policy' was a live candidate: the forfeit is position-dependent and findable, so a harness can screen openings for it.
  Its change of convention - every clock table now reports wall raw AND raw minus 10 ms - is the right fix and is the same discipline as asserting Threads/MultiPV explicitly.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:57:01Z — 25-minute cadence
TWO RESULTS, one a scoping and one the best fixed-point evidence I have had.
  SCOPING (S-C24b): my own start-2 game ran 190 PLIES WITH NO FORFEIT (final clocks white 1,506 / black 822 ms), so seat 27's 144-178 forfeit is machine- or mixture-dependent, not a property of the opening alone. AND I CORRECTED MY OWN FIRST ATTEMPT: that run ended at 97 plies by a THREE-FOLD CLAIM - before the window the claim is about - and my harness initially printed 'does not reproduce', which would have been a FALSE REFUTATION. The verdict logic now distinguishes 'ended too early to test' from 'ran past the window and did not reproduce'.
  THE FIXED POINT, SEEN LIVE (S-F76): black's clock declined from 6,000 ms to a low of 673 ms at ply 179, then ROSE to 822 ms by ply 190 - the last 11 plies had a NEGATIVE net drain, because at a low clock the hard limit falls below the 60 ms increment and each move gains time. That is the fixed point behaving exactly as the arithmetic predicts, and it is the FIRST TIME I have seen the recovery happen in a live game rather than in an iteration. Average net drain 54.5 ms/move over the game, inside seat 27's corrected 68.6-71.7 band and near my 69.2.
  So the honest summary of the forfeit question: it needs the clock to keep draining below the increment, and the engine's own hard limit prevents that past ~110 ms. A forfeit on a real machine therefore needs either a much lower starting clock or a pathological run of hard-limit cuts - which is exactly why seat 27 saw one and I did not.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:58:42Z — 25-minute cadence
A FORFEIT IS IMPOSSIBLE FROM ANY STARTING CLOCK AT THIS INCREMENT (S-F77) - the fixed point tested as a live-game PREDICTION and confirmed 4 of 4.
  Start 600 -> 56 plies, final 1,556/1,471 ms (lowest 562); start 300 -> 1,481/1,302 (lowest 264); start 150 -> 1,456/1,213 (lowest 149); start 100 -> 1,463/1,200 (lowest 100). 4 of 4 ended with BOTH CLOCKS ABOVE THEIR START, 0 forfeits.
  The 100 ms case is the strong one: that is BELOW the 110 ms worst-case floor, and both clocks still climbed to ~1,200-1,460 ms, because at a low clock the hard limit falls below the 60 ms increment and every move GAINS time. Median depth 15 in all four, so the engine was genuinely searching rather than defaulting.
  So a forfeit needs a sustained run of hard-limit cuts that a game from these clocks does not produce - which is exactly why seat 15's and seat 27's forfeits are machine- and position-specific rather than a property of the control. That closes the forfeit question with evidence instead of attribution.
  AND THE METHOD LINE YOU ASKED FOR (S-F78): 'a zero on a claim's window is not a refutation if the run ended early - say ENDED TOO EARLY TO TEST.' My first attempt ended at 97 plies by a threefold claim, before the 144-178 window, and printed 'does not reproduce' - a would-be FALSE REFUTATION of a correct claim. The harness now has three verdicts, not two: confirmed, refuted, and INCONCLUSIVE-because-the-run-ended-before-the-window, with the ending reason recorded. Same family as the two-guards and sample-size rules: the number was real, the SCOPE of the test was too narrow to touch the claim, and only the harness's own bookkeeping can tell the difference.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### FIFTH UPDATE — the forfeit question closed with evidence, and the fixed point as a live prediction

**A forfeit is impossible from any starting clock at the 60 ms increment (S-F77).** Four starting clocks,
PC r15 + PC20 / Threads 1 / Hash 16 / winc=binc=60 / cold, startpos:

| start | plies | final white / black | lowest | forfeit |
|---|---|---|---|---|
| 600 | 56 | 1,556 / 1,471 | 562 | none |
| 300 | 56 | 1,481 / 1,302 | 264 | none |
| 150 | 56 | 1,456 / 1,213 | 149 | none |
| **100** | 56 | **1,463 / 1,200** | 100 | **none** |

**4 of 4 clocks ended ABOVE their start; 0 forfeits.** Starting at **100 ms — below the 110 ms worst-case
floor — both clocks climbed anyway**, because at a low clock the hard limit falls under the increment and each
move gains time. Median depth 15 throughout, so the engine was searching, not defaulting.

**Consequence:** a forfeit needs a sustained run of hard-limit cuts that a game from these clocks does not
produce. That is why seat 15's and seat 27's forfeits are **machine- and position-specific**, not a property of
the 6 s + 0.06 control — and the thread therefore closes on a measurement rather than on one seat's word
against another's.

### THE FIFTH SELF-CORRECTION, and the method line it produced (S-F78)

My first attempt to test seat 27's 144–178-ply forfeit **ended at 97 plies by a threefold claim** — before the
window — and my harness printed "does not reproduce". That would have been a **false refutation of a correct
claim**. The harness now distinguishes **three** verdicts: confirmed, refuted, and **"ended too early to test"**,
with the ending reason recorded.

The family this belongs to, all from tonight, all the same shape — the number was real and the *reading* was
wrong:
1. S-F19 — a board that was not discriminating (correct scores, wrong conclusion).
2. S-C10 → S-C10b — a 60-position sample that gave the wrong sign; the full 353 reversed it.
3. S-F63 — a single out-of-band reading I called a boundary; six repeats showed it was a one-off.
4. S-F74 → S-F74b — a comparison that changed the sample as well as the variable, so the effect was confounded.
5. S-F78 — a test that ended before the window it was testing, read as a refutation.

### CORRECTION OF EMPHASIS — the 100 ms cell leads

The strongest cell in S-F77 is the **100 ms** start, and it should be read first, not last:

> **Starting at 100 ms — ten milliseconds BELOW the 110 ms worst-case floor predicted by
> `MoveOverhead + increment*100/TmHardPercent` — both clocks still CLIMBED, to 1,463 ms and 1,200 ms over 56
> plies, with no forfeit.** Median depth 15, so the engine was searching normally.

Why that cell is the one that matters: every other starting clock (600, 300, 150) sits at or above the floor, so
a clock that drifts down from those would still be consistent with a floor somewhere lower. **100 ms is below
the floor, and it rose.** That is the case that shows the mechanism is not merely "the drain slows near the
floor" but **actively negative below it** — at a low clock the hard limit falls under the 60 ms increment, so
each move gains time. Reordered, the table reads:

| start | plies | final white / black | lowest | forfeit |
|---|---|---|---|---|
| **100 ms (below the floor)** | 56 | **1,463 / 1,200** | 100 | **none** |
| 150 ms | 56 | 1,456 / 1,213 | 149 | none |
| 300 ms | 56 | 1,481 / 1,302 | 264 | none |
| 600 ms | 56 | 1,556 / 1,471 | 562 | none |

The conclusion is unchanged and is now anchored where it is strongest: **a forfeit is impossible from any
starting clock at this increment, including from below the floor.**

### THE THREE-VERDICT RULE, as its own method outcome (S-F78)

Kept as a distinct outcome, not folded into "refuted":

| verdict | meaning |
|---|---|
| **confirmed** | the claim's window was reached and the predicted thing happened |
| **refuted** | the claim's window was reached and the predicted thing did not happen |
| **inconclusive — the run ended before the window** | the test did not touch the claim; record the ending reason |

The third exists because my first attempt at seat 27's 144–178-ply forfeit **ended at 97 plies by a threefold
claim** and my harness printed "does not reproduce" — a false refutation of a correct claim. This is the most
reusable thing from the clock work: a zero on a claim's window means nothing if the run stopped before the
window, and only the harness's own bookkeeping distinguishes the two.

## 2026-11-16T23:59:07Z — 25-minute cadence
BOTH CORRECTIONS MADE (S-F79, S-F80).
  1) THE 100 ms CELL NOW LEADS, and the FINAL says why it is the one that matters: every other starting clock (600/300/150) sits at or above the predicted 110 ms floor, so a clock drifting down from those is still consistent with a floor somewhere LOWER. 100 ms is BELOW the floor and both clocks CLIMBED to 1,463 / 1,200 ms over 56 plies with median depth 15. That is what shows the mechanism is not 'the drain slows near the floor' but ACTIVELY NEGATIVE BELOW IT - at a low clock the hard limit falls under the 60 ms increment so every move gains time. The table is reordered 100/150/300/600 and the conclusion is anchored where it is strongest: a forfeit is impossible from any starting clock at this increment, including from below the floor.
  2) THE THREE-VERDICT RULE IS NOW ITS OWN PAGE (S-F80, THREE_VERDICTS_NOT_TWO.md): CONFIRMED / REFUTED / INCONCLUSIVE-because-the-run-ended-before-the-window, the third being the statement that the test did not happen, with the ending reason recorded. It leads with the worked failure: my first attempt at seat 27's 144-178 ply forfeit ended at 97 plies by a threefold claim and printed 'does not reproduce' - a false refutation of a correct claim. The check is ONE COMPARISON (does the run reach the claim's window?) and it is bookkeeping rather than measurement, which is why it is the cheapest of tonight's five corrections to borrow.
  The page also lists all five self-corrections together, since they share the shape 'the number was real and the reading was wrong' - and the first four are fixed by better measurement while the fifth is fixed by bookkeeping.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-16T23:59:30Z — 25-minute cadence
SEAT 06's S-F31 CONFIRMED (S-C25): PC r15 under PC20 and base under S14 evaluate a position IDENTICALLY, 120 of 120 positions, 0 differing, 0 unreadable. Identical FENs only, so seat 16's side-to-move eval trap cannot arise. Sample rows: -325/-26/-351 both builds, 229/-33/196 both builds, -396/-125/-521 both builds.
  WHY IT MATTERS (S-F81), and it is the most useful thing in this confirmation: it divides the swarm's findings cleanly into two classes. EVALUATION findings on base 6b98f217 TRANSFER to the owner's engine, because hce/nnue/total are identical. SEARCH findings - drawn roots, mate distance, depth reached, node counts - need re-testing per build, which is exactly what my own area found: FORGE_FIX_ROOT_DRAWN changed the search and nothing in the parser or the evaluation. A reader can now tell which of the swarm's results apply to the engine he actually plays.
  This is also a positive result for the PC build's construction: the patch changed 11 files and 1,200 lines, and the evaluation of 120 positions is bit-identical afterwards.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### SIXTH UPDATE — the two classes of findings, and which ones reach the owner's engine

**S-C25 / S-F81.** PC r15 (under PC20) and the base build (under S14) evaluate a position **identically: 120 of
120 positions, `hce` / `nnue` / `total` equal, 0 differing.** Identical FENs only, so the side-to-move eval trap
cannot arise.

**Scope, immediately: this is BUILD-independent, not NET-independent.** The 120/120 used the **built-in net**.
File 2 records that the owner's PC plays with **its own trained net** (`NNUEArch true`, king-bucket), where the
search returns through `static_evaluate_v3` before the hand-written evaluation — and **no net file is shared
with the swarm** (a search for `.nnue`/`.bin` under both trees finds none), so **that mode is untestable on this
machine by any seat.** Read "evaluation transfers" as *between builds on the same net*.

Also worth knowing when reading an `eval` line: `UseNNUE false` gives `hce -42  nnue 0  total -42`, so the three
numbers decompose as **hand-written plus net contributions**, not three independent measurements.

That single fact sorts every finding in the swarm:

| class | reaches the engine the owner plays? | evidence |
|---|---|---|
| **evaluation** — `hce`/`nnue`/`total`, eval terms, evaluation symmetry | **YES** | identical 120/120 across builds |
| **search** — drawn roots, mate distance, depth, node counts, clock behaviour, PV truncation | **NO — re-test per build** | `FORGE_FIX_ROOT_DRAWN` changed the search and nothing else (S-F37, S-F41) |

So a **base-tree evaluation result is a statement about the owner's engine**; a **base-tree search result is
not**. That is the practical rule a reader needs before carrying any of tonight's findings across, and it came
out of a check that was only meant to confirm someone else's number.

It is also a good sign for the patch itself: **11 files and ~1,200 lines changed, and the evaluation of 120
positions is bit-identical afterwards.**


### SCOPE OF THE TWO-CLASS SPLIT — stated before it is over-read

Two things make S-C25/S-F81 meaningful, and one limit bounds it.

**(a) Identical FENs only.** The comparison used the same FEN string on both builds, never a position and its
mirror, so **the side-to-move-relative `eval` trap (seat 16's S-C5) cannot arise**. That is why 120 of 120 is a
real comparison rather than an artefact of comparing a position against its colour-flip.

**(b) A good characterisation of the patch: 1,200 changed lines, evaluation bit-identical.** Saying it plainly
rather than as a control note — the PC r15 patch changes **11 files and ~1,200 lines**, and after it the
evaluation of 120 positions is **bit-for-bit unchanged** (`hce`, `nnue` and `total` all equal). A patch that
large that leaves evaluation exactly intact is doing its work where it says it does, in the search.

**(c) THE LIMIT, which I cannot test here: this holds for the BUILT-IN net only.** File 2 records that the
owner's PC plays with **its own trained net file** (`NNUEArch true`, a king-bucket net), and in that mode the
search returns through `static_evaluate_v3` before the hand-written evaluation. **No net file is shared with the
swarm** (my search for `.nnue`/`.bin` under both trees finds none), so the owner's net-file mode is untestable on
this machine. Therefore:

- **with the built-in net** — confirmed: evaluation identical across builds, so base-tree evaluation findings
  transfer;
- **with the owner's own net** — **untested**, and the net is not shared, so it cannot be tested by any seat.

The honest form of the two-class split is: *evaluation findings transfer between builds on the same net*, and the
owner's net is a different net. A reader should read "transfers" as **build-independence**, not as
**net-independence**.

## 2026-11-16T23:59:59Z — 25-minute cadence
BOTH POINTS KEPT, AND ONE LIMIT I HAD TO ADD BEFORE THE SPLIT IS OVER-READ (S-F82).
  (a) IDENTICAL FENs ONLY is now stated as part of what makes 120/120 meaningful: the comparison never used a position against its colour mirror, so seat 16's side-to-move-relative eval trap cannot arise.
  (b) THE PATCH-QUALITY POINT, said plainly rather than as a control note: the PC r15 patch changes 11 files and about 1,200 lines, and after it the evaluation of 120 positions is BIT-FOR-BIT unchanged in hce, nnue and total. A patch that large leaving evaluation exactly intact is doing its work where it says it does, in the search.
  (c) THE LIMIT: my 120/120 used the BUILT-IN net. File 2 records that the owner plays with HIS OWN trained net, where the search returns through static_evaluate_v3 before the hand-written evaluation - and NO NET FILE is shared with the swarm (a search for .nnue/.bin under both trees finds none), so that mode is untestable here by me or by any seat. So the honest form is: EVALUATION FINDINGS TRANSFER BETWEEN BUILDS ON THE SAME NET, and the owner's net is a different net. 'Transfers' means BUILD-INDEPENDENT, not NET-INDEPENDENT.
  Also noted: UseNNUE false gives 'hce -42 nnue 0 total -42', so the three numbers decompose as hand-written plus net contributions rather than being independent - worth knowing when reading an eval line.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-17T00:03:27Z — 25-minute cadence
SEAT 13's S-F21 AND S-F22 CONFIRMED (S-C26), and S-F22 turns out to be the stronger form of my own clock rule (S-F83).
  S-F21: 8 clock values (1 s to 12 s) x 5 position types, fresh process per cell - distinct node counts per position are 5/6/5/6/4 out of 8 (startpos, middlegame, tactical, rook endgame, queen endgame). EVERY position type plateaus, so it is an allocator property and not a coincidence, exactly as seat 13 concluded.
  S-F22: of 780 pairwise comparisons, 17 had equal node counts and ALL 17 had the same bestmove; 0 groups had more than one distinct move. So an equal node count identifies the same search.
  THE STRONGER FORM (S-F83): I showed the plateau EXISTS (S-C15); seat 13 shows what it MEANS. Practical consequence for a match harness - you do NOT need to re-run to confirm a clock result is on the same rung; compare the NODE COUNT, and if it matches, the move and therefore the whole search matches too. That makes the S-F64 sweep cheaper than it looked: the sweep identifies the rung, the node count certifies any later run as being on it.
  ALSO: moved the build-vs-net scope note UP so it sits directly beside the 120/120 result rather than in a later section, as you asked, with the eval decomposition note (UseNNUE false gives hce -42 / nnue 0 / total -42, so the three numbers are hand-written plus net contributions, not independent) beside it.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### SEVENTH UPDATE — the clock rule made operable

Two confirmations this stretch, both of seat 13's:

- **S-C26 / S-F21:** the plateau is **general across position types** — 8 clock values × 5 types (startpos,
  middlegame, tactical, rook endgame, queen endgame) give **5 / 6 / 5 / 6 / 4 distinct node counts out of 8**.
  Every type plateaus, so it is an allocator property, not a coincidence.
- **S-C26 / S-F22 → S-F83:** **an equal node count means an equal move** — 17 of 17 equal-node pairs shared
  their bestmove, 0 groups disagreed across 780 pairwise comparisons.

**The second one turns my clock rule into something a harness can act on**, and `CLOCK_REPRODUCIBILITY_RULE.md`
now carries it as a numbered step:

> Sweep once to identify the plateau, then **certify any later run by comparing its node count** — if the count
> matches the plateau, the move and the whole search match too. The sweep becomes a one-off cost, not a per-run
> one.

So the rule is no longer "sweep and repeat 2-3 times every time"; it is "sweep once, then verify cheaply against
a node count". That is the difference between a procedure nobody follows and one that costs a single number per
run.

### EIGHTH UPDATE — the clock rule now leads with the operational sentence

`CLOCK_REPRODUCIBILITY_RULE.md` opens with:

> **Sweep once to identify the rung, then certify a run with a single node count.**
>
> A clock budget is reproducible only to a **plateau** — a band of clocks that all give the same answer. Sweep
> once to find it, then check any run against it by comparing its **node count**. An equal node count means an
> equal move, so a matching count certifies the whole search without re-running it (17 of 17 equal-node pairs,
> 0 disagreements across 780 comparisons — S-C26 / S-F83).
>
> The sweep is a **one-off cost**, not a per-run one.

The licence for that sentence is the measurement behind it: **780 pairwise comparisons, 17 equal-node pairs,
17 identical bestmoves, 0 groups disagreeing**, across five position types and eight clocks. Without that zero,
the sentence would be a suggestion; with it, a harness can trust one number instead of re-running a search.

That is the shape most of tonight's useful results ended in — a measurement first, then the sentence that makes
it usable — which is why the rule pages and the evidence files are kept together on the branch.

## 2026-11-17T00:08:13Z — 25-minute cadence
SEAT 20's S-F50 PARTIALLY CONFIRMED, AND THE SHAPE OF IT CORRECTED (S-C27, S-F84).
  The grid, PC r15 + PC20, Threads 1, go wtime 5000 btime 5000, idle, 5 fresh processes per cell: MultiPV 1/Hash 16 -> 0/5 zero (170k-289k nodes, g7g6); MultiPV 1/Hash 2048 -> 0/5 (170k, g7g6); MultiPV 4/Hash 16 -> 0/5 (165k, g7g6); MultiPV 4/Hash 2048 -> 220 NODES, moves b8a8/d5d4; MultiPV 8/Hash 16 -> 0/5 (211k, g7g6); MultiPV 8/Hash 2048 -> 143-220 NODES, move b8a8.
  So on an idle machine the collapse needs BOTH a high MultiPV (>=4) AND a large Hash (2048) - which matches seat 20's S-F50 combination and its S-C30 narrowing. Single-parameter changes are clean.
  BUT THE SHAPE IS DIFFERENT FROM '0-node': what I observe is 143-220 nodes with a DIFFERENT MOVE, and only one run had no readable node line at all. So the pathological cell returns a move with essentially no search behind it - the same hazard whether it prints 0 or 220. My checker counted only exact zeros and would have said 'no collapse in any cell', which would have been a wrong reading of my own data until I looked at the node counts.
  THE USEFUL SIGNAL FOR THE OWNER (S-F84): healthy cells print 165k-289k nodes and always g7g6; pathological cells print 143-220 nodes and a different move. A user does not need to wait for a printed 0 - a THREE-DIGIT NODE COUNT on a 5-second search is the signature, and the move has already changed. Action unchanged: MultiPV 1 at any Hash, or Hash <= 16 MB with MultiPV > 1.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### THE CLOCK THREAD, CLOSED ON FOUR LEGS

Summarised here because it is the one thread that ran end to end, and it shows the method working:

1. **The fixed point, derived from the engine's own constants.** `floor = MoveOverhead + increment*100 /
   TmHardPercent` = **110 ms** (111 with integer division), reached independently by seat 28's S-F44 and by the
   coordinator's argument (S-C12b, S-C14). My earlier 493 ms is corrected — it iterated with the observed spend
   rather than the cap the bound is defined over.
2. **The fixed point, seen live in a game.** Black's clock fell to **673 ms at ply 179 and rose to 822 ms by ply
   190** — a negative net drain at low clock (S-F76).
3. **A forfeit shown impossible from any starting clock.** Four starts (600/300/150/**100** ms), **4 of 4 rose,
   0 forfeits** — the 100 ms case sitting *below* the floor and still climbing (S-F77, S-F79).
4. **The plateau generalised and made certifiable.** 5 position types × 8 clocks give **5/6/5/6/4 distinct
   outcomes**; and **an equal node count means an equal move** (17 of 17 pairs, 0 disagreements in 780), so a
   run is certified by one number instead of a repeat (S-C15, S-C26, S-F83, S-F64).

**"A measurement first, then the sentence that makes it usable"** is the shape those four legs share, and it is
the shape most of tonight's useful results ended in — which is why every rule page on this branch sits beside
the evidence file that licenses it rather than standing alone.

## 2026-11-17T00:08:34Z — 25-minute cadence
RECORDED THE SIXTH SPECIES OF SELF-CORRECTION, and it is genuinely different from the other five (S-F85).
  The first five are about SAMPLES, SCOPE AND CAUSALITY - in each the measurement covered the wrong ground. This one is about SUMMARISATION, and it happened inside my own harness: my zero-node checker reduced each result to 'zero = (nodes == 0)', so when the pathological MultiPV/Hash cells returned 143-220 nodes with a CHANGED MOVE it scored them HEALTHY. Had I reported the flag I would have written 'no collapse in any cell' while the correct raw numbers sat in the same record, in the very columns the flag was derived from.
  THE RULE, now in THREE_VERDICTS_NOT_TWO.md alongside the others: 'A derived boolean is a CLAIM about the data, not a summary of it. When a flag says nothing is here, re-read the columns it was derived from before reporting a negative.' It is cheaper to apply than any of the other five, and it caught a wrong conclusion in the same session that produced it - the collapse was visible in the node and move columns all along.
  Kept your other two points as stated: the three-digit-node-count-plus-changed-move signature is the owner-facing signal, and the plain statement that 5 runs per cell cannot catch a 1-in-10 event means seat 20's exact zero is NOT refuted.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

## 2026-11-17T00:09:38Z — 25-minute cadence
I RAN SEAT 13's S-F23 STRUCTURAL CHECK ON MY OWN FINDINGS.md AND IT FOUND REAL DEFECTS (S-F86) - five across three rounds, all in my own artefacts.
  ROUND 1, real defects: a TRUNCATED ROW (S-F77 had lost its evidence and status cells, so its sentence ended where the evidence should begin) and a DUPLICATE ID (two different rows both labelled S-C3 - the second is now S-C3b). Both fixed.
  ROUND 2, real defect: a row containing a literal '||' from a C++ snippet (is_repetition() || is_insufficient_material()), which splits the cell when rendered. Escaped.
  ROUNDS 2-3, two bugs in THE CHECKER ITSELF: it first asserted the wrong expected width and flagged 115 of 117 rows; then it compared PIPE counts against CELL counts (a k-cell row has k+1 pipes) and flagged one perfectly good row. Seat 13's companion lesson is exactly this - when a checker flags everything, or flags one thing persistently, suspect the checker's own assumption before the file.
  FINAL STATE: 117 rows, 0 wrong cell counts, 0 duplicate ids. The checker is committed as check_findings_table.py with its own two-bug history in the docstring, so the next person to touch the file inherits the lesson rather than just the tool.
  Notably this is the third time tonight a defect was found in my own artefact rather than the engine: the committed .pyc files, the stray root STATUS.md, and now three malformed rows. Each was found by looking, not by assuming.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### NINTH UPDATE — a structural check of my own file, and the sixth species made concrete

Seat 13's S-F23 ("a markdown table is not validated by looking at it") applied to `FINDINGS.md` found **five
defects across three rounds, all in my own artefacts**:

| round | defect | where |
|---|---|---|
| 1 | **truncated row** — evidence and status cells missing | S-F77 |
| 1 | **duplicate id** — two rows both labelled S-C3 | S-C3 / now S-C3b |
| 2 | **unescaped `\|\|`** from a C++ snippet, splitting the cell | S-F31 |
| 2 | checker bug — wrong expected width, flagged 115 of 117 | `check_findings_table.py` |
| 3 | checker bug — compared **pipes** against **cells** (a k-cell row has k+1 pipes) | `check_findings_table.py` |

**Final: 117 rows, 0 wrong cell counts, 0 duplicate ids.**

The two checker bugs are the **sixth species** in its most literal form: the flag was wrong and the data was
right. The first said 115 of 117 rows were broken; the second persistently flagged one good row. Both are the
sentence that leads that species — *a derived boolean is a claim about the data, not a summary of it* — applied
to the tool rather than the result.

The checker is committed with its own two-bug history in the docstring, so the lesson travels with the tool.

**Counted plainly: this is the third time tonight a defect was found in my own artefact rather than the engine** —
the committed `.pyc` files, the stray root `STATUS.md`, and now three malformed rows. Each was found by looking,
and the structural check is the cheapest of the three to institutionalise: it runs in a second and needs no
engine.

### TENTH UPDATE — three defects in my own artefacts, counted and each verified fixed

Not engine defects — **defects in my own working artefacts**, which is a different and worth-stating category:

| # | defect | found by | fixed, and verified |
|---|---|---|---|
| 1 | **four committed `.pyc` bytecode files** — the rules say text only | listing every non-text extension on the branch | removed with `git rm --cached`, deleted from the tree, `.gitignore` (`__pycache__/`, `*.pyc`) added; **`ls .gitignore` confirms it is present and the branch is text-only** |
| 2 | **a stray `STATUS.md` in the repository root** — outside my folder | checking `git status` before a push | untracked, so never in history; deleted; **`ls /agent/repos/dwqww/STATUS.md` → no such file** |
| 3 | **three malformed rows in `FINDINGS.md`** — a truncated row, a duplicate id, an unescaped `\|\|` | seat 13's S-F23 structural check, applied to my own file | repaired; **checker reports 118 rows, 0 wrong cell counts, 0 duplicate ids** |

**Why this category is worth a line in a report about an engine:** an agent's output is only as trustworthy as its
artefacts, and all three were invisible from the engine's side. A node count can be perfect while the report that
carries it is malformed, contains a binary, or sits in the wrong folder — and none of the engine tests would ever
notice. Each was found by **looking at the artefact**, not by assuming it was fine.

The pattern across all three: the defect was in something I had created and not re-read. The structural checker
is the cheapest of the three to institutionalise — it runs in a second and needs no engine — which is why it is
committed alongside the findings rather than kept as a personal habit.

## 2026-11-17T00:11:03Z — 25-minute cadence
SEAT 25's S-F37 CONFIRMED AND ITS OWN CAVEAT CLOSED (S-C28) — and the answer is the worse of the two readings.
  Seat 25 reported that depth/movetime clamp 0 upward but flagged that its probe was a SCOPE result, not a 0-versus-ABSENT one. I tested 0 against the field being ABSENT, which is what a harness actually needs:
    go depth 0 -> DEPTH 1, 155 nodes.  go depth 5 -> depth 5.  NO depth limit (go infinite stopped at 1 s) -> DEPTH 21, 1,493,714 nodes.
  So 0 and ABSENT differ completely: 0 clamps to ONE PLY while omitting the field searches freely. A harness that sends depth 0 to mean 'no limit' gets a 21-fold depth loss on my board (S-F87).
  Also confirmed: go movetime 0 -> depth 6, 993 nodes, 1.3 ms (a floor, not zero time); go nodes 0 -> answered with f5f4 and no depth/nodes line at all, against the control go nodes 20000 -> depth 10, b6b5. So three of the four limit fields clamp 0 upward and the fourth declines to search.
  THIS COMPLETES A FAMILY of three settings a harness sends to mean 'unset', each doing the opposite: movestogo 0 (sudden-death branch, 8.4x the plan of omitting it), depth 0 (one ply vs depth 21), and MultiPV above 1 (divides the node budget, depth 10 -> 7). All three now sit in MEASUREMENT_TRAPS.md with the same rule: to mean 'no limit', OMIT THE TOKEN — never send 0.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### ELEVENTH UPDATE — the traps page reduced to its two-column shape

`MEASUREMENT_TRAPS.md` now ends in the form that made it usable:

> **To mean no limit, omit the token.**

| what a harness sends to mean "unset" | what it actually does |
|---|---|
| `movestogo 0` | selects the **sudden-death** branch: **482 ms** per move instead of **57 ms** — 8.4x the plan of omitting the token |
| `depth 0` | clamps to **one ply**: depth 1 in 155 nodes, against **depth 21** with the field absent — a 21-fold loss |
| `MultiPV` above 1 | **divides the node budget**: depth 10 → 7 at 20,000 nodes, depth 8 → 2 on `softnodes 2000` |
| `Threads` above 1 | **varies by design**: score, node count and sometimes the move differ run to run |

Two columns, no third: *what you might send* and *what it does instead*. The measurements live in the row, not
in a separate column, so the table can be read at a glance and each row still carries its number.

**The page is now four traps in a consistent order** — MultiPV, movestogo, depth, Threads — each with its own
section, then this table, then the guard. Nothing is left appended out of order.

### TWELFTH UPDATE — the best argument in the run for second-seat work

`MEASUREMENT_TRAPS.md` — the most compact actionable page I produced — is **almost entirely built out of
confirming other seats**, not out of new work of my own:

| trap | whose finding | my contribution |
|---|---|---|
| `MultiPV` above 1 divides a node budget | **seat 02** (S-F9 / S-F10) | independent confirmation on my own board, and the sublinear shape |
| `movestogo 0` selects sudden-death | **mine** (S-F62) | the one trap from my own work |
| `depth 0` clamps to one ply | **seat 25** (S-F37) | the **0-versus-absent** test that closed its own stated caveat |
| `Threads` above 1 varies by design | already in the brief (file 6, seat 04) | folded in for completeness |

**Three of the four rows are another seat's finding that became actionable only after a second seat tested it.**
Seat 25's row is the clearest case: it reported the clamp but said honestly that its probe was a scope result,
not a 0-versus-absent one — and the 0-versus-absent test showed the gap is **worse** than its scope reading
(`depth 1` against `depth 21`).

That is the argument for the confirmation rule, and it is stronger than any number of confirmations that merely
agree: **a second seat does not just check a claim, it can find the claim is under-stated.** A rule that only
policed for errors would have passed seat 25's finding through unchanged and left the sharper version unwritten.

## 2026-11-17T00:12:06Z — 25-minute cadence
SEAT 05's S-F63 CONFIRMED EXACTLY, AND ITS INFERENCE TURNED INTO A MEASUREMENT (S-C29, S-F88).
  Every number reproduces on PC r15 + PC20 / Threads 1 / Hash 16 / OwnBook false, fresh process per row: 5,000 -> cp 3725 d8; 10,000 -> cp 3935 d9; 15,000/20,000/30,000 -> cp 4056 d10, ALL THREE IDENTICAL at 10,515 nodes; 50,000 -> mate 11 d11, 44,749 nodes, 18-ply PV needing 21; 80,000 -> mate 7 d13, 13/13; 250,000 -> mate 7 d14, 13/13.
  THE PART SEAT 05 COULD ONLY INFER: it deduced truncation by comparing PV length to the plies a mate needs. I SLICED each PV from the info line and REPLAYED it with python-chess. The 50,000-node PV does NOT reach mate - it ends after 18 plies without checkmate - while the 80,000 and 250,000 PVs DO, checkmate at pv ply 13. So the truncation is real by replay, and the later mate scores are honest.
  WHY IT SURVIVED SO LONG (S-F88): the answer is CORRECT either side of a narrow band and OVER-CLAIMED inside it. Any spot-check at a different budget shows a healthy mate - 80,000 and 250,000 both give mate 7 with a PV that mates. 50,000 nodes is one of the OWNER'S MATCH BUDGETS, so this is on his path.
Next: continue confirming while the window runs to 2026-11-17T10:18Z.

### THIRTEENTH UPDATE — a defect on the owner's path, confirmed and explained

**S-C29 / S-F88.** Seat 05's S-F63 reproduced **exactly**, and I could upgrade its inference into a measurement.

Board `r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b`, PC r15 + PC20 / Threads 1 / Hash 16:

| budget | score | depth | nodes | PV plies | plies a mate needs | PV reaches mate? |
|---|---|---|---|---|---|---|
| 15,000 / 20,000 / 30,000 | `cp 4056` | 10 | **10,515 (all three identical)** | 10 | — | — |
| **50,000** | **`mate 11`** | 11 | 44,749 | **18** | **21** | **NO** |
| 80,000 | `mate 7` | 13 | 74,525 | 13 | 13 | **YES** |
| 250,000 | `mate 7` | 14 | 138,869 | 13 | 13 | **YES** |

Seat 05 deduced the truncation from PV length. I **sliced the PV from the info line and replayed it**: the
50,000-node PV ends after 18 plies **without checkmate**, while the 80,000 and 250,000 PVs reach mate at ply 13.
So the truncation is real by replay and the later mate scores are honest.

**Why it survived so long:** the answer is **correct either side of a narrow band and over-claimed inside it**. A
spot-check at any other budget shows a healthy mate — only a ladder finds it.

**And 50,000 nodes is one of the owner's three match budgets**, so this is the most consequential confirmation I
made tonight: a mate distance his engine cannot justify at a budget he actually uses.
