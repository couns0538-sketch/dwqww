## 2026-11-16T22:28Z - COST QUANTIFIED (S-F20); win positions unaffected; repair consequence stated

Task 1 (cost): scanned 17 candidates from G, required the opponent's reply to be a clock-RESETTING move before
counting a cost. 8 of 17 pass: cp 0 at clock 99 where clock-0 is -40..-1039 cp, and the opponent refuses with a
capture or pawn push (verified mechanically: 4 pawns, 4 captures, clock 0 afterwards). WINNING positions are NOT
affected (+2232 -> +1965, +423 -> +417, +2570 -> +2563), so only the losing side is hurt - consistent with the
mechanism, since a 0-valued draw line is attractive only to the side that is worse.
NOT claimed: that a game result changes. In all 8 the side was already worse; I hunted a "real draw thrown away"
case and every candidate I verified had the opponent NOT resetting, i.e. the engine was right there.

Task 2 (repair consequence): remove the fifty-move test from is_draw entirely, do not move it to the root -
terminality tests must be decidable without searching, and a claimable draw is not. Risks stated: quiet lines to
the horizon are re-valued (slightly overvaluing about-to-be-drawn positions, the same direction as the PC's own
root-drawn fix), and 341-node answers become 15k-19k nodes. For the forced case the legitimate predicate is
"clock >= 100 AND neither side has a capture or pawn move". Not implemented; patch unchanged.

Also in this cycle: S-F15/S-F16 mechanism, S-F17 predictions, S-F18/S-F20 cost, S-F19 repair proposal,
S-C3 (seat 06 S-F21, exact), S-C4 (file 5 table, exact). Next: cycle - other seats' unconfirmed finds.
## 2026-11-16T22:27Z - MECHANISM FOUND (instrumented build), and a correction of my own reasoning

Instrumented build done as the coordinator asked: scratch copy, stderr-only prints behind FORGE_CLOCK99_DEBUG,
EXPERIMENT patch committed as text only (debug/FORGE_EXPERIMENT_clock99_debug.patch.txt), never applied to the
repository source. Ran the three cases: breaking@99, non-breaking@99, control@98.

WHAT THE INSTRUMENTATION SHOWED
- NO root shortcut fires: `root_drawn=0`, all 27 candidates present, and `[DBG ROOT ITER SEARCHED] depth=1..6
  score=0 pv_len=1`. So S-F14's "root shortcut" mechanism was wrong (the observation was right). Corrected.
- 109 `is_draw TRUE` lines, every one `clock=100 fifty=1`: the draw test fires on the CHILDREN, not the root.
- Every root move searched alone: 18 quiet moves -> exactly `cp 0` with a 1-ply PV; 9 reset moves -> -212..-488.
  So the root's 0 IS the max of its children - the arithmetic is consistent.

THE RULE, CHECKED (this is where I had been wrong too)
The fifty-move draw is CLAIMABLE, not automatic. python-chess: at clock 100 `is_game_over(claim_draw=False)` is
False, 25 legal moves, and black simply plays h7h6 -> clock 0, game continues. A winning side never claims.
So white's quiet move does NOT secure a draw and `cp 0` at clock 99 IS WRONG (my original S-F3 stands). I had
briefly written the opposite in is_zero_right.py; that line is withdrawn in the same commit (debug/CORRECTION.md).

MECHANISM, ONE SENTENCE
`Worker::is_draw` scores a CLAIMABLE fifty-move draw as if it were FORCED: the clock-100 child returns 0, the root
takes 0 as its maximum, so at clock 99 a position worth -155 cp is reported as a draw and the engine plays a quiet
shuffle the opponent can simply decline by resetting the clock.

THREE FALSIFIABLE PREDICTIONS, ALL CONFIRMED (S-F17)
- clock 100 with resets available -> also cp 0 (251 nodes) - the fault is not specific to 99.
- clock 100 with NO reset possible anywhere (K+R vs K+R): cp 0 in 32 nodes - CORRECT there. This is the
  discriminating control: the clock-100 test is wrong exactly when a reset exists, which is the
  claimable-vs-forced distinction.
- board whose best moves are resets stays non-zero at clock 99 (cp 549 in 3,918 nodes).

NEXT: keep cycling - next area-5 repetition with a new seed, and re-check other seats' unconfirmed finds.
## 2026-11-16T22:23Z — PC build integrated; coordinator's three tasks done

Built PC r15 from FABLE_TO_swarm_5 (patch sha256 matches, no rejects, -DFORGE_MATE_ALPHA_GUARD=1).
All three rows of file 5's honesty table reproduce exactly (312866/862329/3024920/4865609;
242796/656517; 278024/587276). Read files 3, 4, 5.

Coordinator's three tasks, all answered:
1. REACHABILITY: PROVEN by a legal 99-ply list (reach.txt, verify_walk.py replays and asserts every move);
   PC build answers cp 0 in 661 nodes there vs -15 cp in 32,461 at clock 0. (S-F11)
2. BASE vs PC: break is identical on both builds under default/S14/PC20 — predates r15, not one of the six
   options (S-F12). Onset exactly 99 (S-F13: clock alone is not enough — start position at clock 99 is fine).
   Shape is a root shortcut but the mechanism is UNIDENTIFIED: is_draw (>=100), root_drawn (insufficient
   only) and rule50_damped_static (inert) are all refuted by their own source. Recorded, not guessed (S-F14).
3. Cosmetic: mate 0 on a checkmated root vs cp 0 on a stalemated root, and 64 phantom info lines on a
   terminal root — both survive on the PC build, both re-measured with a plant passing (S-F6, S-F7).

Earlier finds re-run on the PC build: S-F1 and S-F8 are REPAIRED there (mate -4 and mate -8, correct).
Next: continue the cycle — check other seats' unconfirmed finds, then the next area-5 job.
## 2026-11-16T22:18:48Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:48Z

Resuming under the owner's 12-hour continuation. Seat 25 unchanged (area 5, PVs and scores).
All area-5 jobs 1, 2, 3 are done, plus a second and third run of job 1, plus two independent
reproductions of other seats (S-C1 seat 06 S-F10, S-C3 seat 06 S-F21) and one of seat 10's rule (S-C2).

Immediate plan, in this order:
1. Read every unread FABLE_TO_swarm_N.md from the handoff branch, lowest N first (file 5 = the PC build).
2. Build the PC engine as file 5 says (separate copy, -DFORGE_MATE_ALPHA_GUARD=1), check its bench numbers.
3. Re-run my own finds on the PC build under settings PC20, recording build+settings in every finding line.
4. THE CYCLE: check other seats' unconfirmed finds, else the next job.

Results just before this block (already committed):
- S-F10: the wrong mate score is NOT state; a fresh process reproduces it, and it overrides a correct
  deeper result in the same process.
- NEW and important: S-F8's mate score at depth 20 is HASH-DEPENDENT (mate -7 at 64/256 MB, mate -8 at
  smaller sizes), while S-F1's is stable (mate -5 at every size). Evidence: job1c/hash_dependence.txt.
- verify_all.py: 8/8 headline claims re-verified from scratch (verify_all.txt).
## 2026-11-16T22:00:00Z — all area-5 jobs done; this is my complete state

seat: 25 | area: 5 (principal variations and scores) | seed: 2501 (run 2 used 2511)
branch: for-fable-and-opus/swarm-25 | folder: forge-combo29/swarm/25/

ENGINE: build 6b98f217, release /home/ubuntu/build/release/forge,
sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83.
HONESTY all four match: 312866 / 862329 / 3024920 / 4865609 (HONESTY.txt).
Sanitizer build /home/ubuntu/build/asan/forge: 35 __asan_ + 15 __ubsan_ symbols.

FINDINGS (all with a command that shows them again, all in FINDINGS.md):
- S-F1 CRITICAL: 8/8/1p6/8/p3p3/8/2Kpk3/8 w says `mate -12` at depth 12..16. The engine's OWN depth-28 PV
  checkmates in 8 plies (verify_pv_line.py: "checkmate after 8 plies = mate in 4 moves"), so the true answer
  is mate -4 and the shallow score is wrong by 8 moves.
- S-F2: that root's score wanders -12 / -9 / -6 / -5 / -4 with depth.
- S-F3 + S-F4 + S-F5 CRITICAL: at halfmove clock 99 the engine reports cp 0 at every depth and at
  `go nodes 50000`, on boards with 6-11 legal clock-resetting moves; boundary is exactly 98 (good) -> 99 (0);
  EvalRule50Damp, depths 1..30 and UseNNUE false change nothing; and the clock-99 MOVE is -40/-999/-160 cp
  worse than the engine's own clock-0 move.
- S-F6: a checkmated root reports `score mate 0` while a stalemated root reports `cp 0` (inconsistent).
- S-F7: on a terminal root, `go nodes`/`go movetime` emit 64 info lines at 0 nodes.
- S-F8: the mate-PV defect also hits a middlegame position (score mate -9, 15-ply PV, not a mate).
- S-C1: confirms seat 06's S-F10 depth-10 result with the correction that it does not generalise to depth 12.
- S-C2: independently reproduces seat 10's Clear Hash / ucinewgame rule on my build.

PROCESS AUDITS (both coordinator broadcasts answered, evidence committed):
- 19-F12: my harness is SAFE (stdin open, read to bestmove). Pipelined go+quit does fabricate a2a3.
  audit in check_19F12/. No recorded result of mine used that pattern.
- Clear Hash: never used by me. ucinewgame verified cold on this build (18407 x3 = fresh processes).
  No table of mine needs a warm relabel. audit/warm_cold_audit.txt.
- Rule 1 (a zero needs a planted one): done for job 1 (illegal PV 5/5, wrong mate 5/5), job 2 (clock 98 vs 99)
  and job 3 (planted ASan fault counted 120 times by the same runner).
- Checkers now FAIL LOUDLY (exit 3) on empty input or an unparsed score.

MISTAKES OF MINE, RECORDED NOT HIDDEN:
- job3 first root list: 15 of 20 FENs were not terminal; engine was right, my FENs were wrong. Regenerated
  and verified, re-ran, 60/60 bestmove 0000. Both runs kept in job3/real and job3/final.
- mated.py had a double-pop bug; fixed, S-F1 re-verified with the fixed version (still mated in 4).
- dtm_fast.py and true_mate*.py/dt* are NOT correct (dtm_fast says "no mate" on a position with a verified
  mate in 4); kept in the tree, used for nothing.
- rule50_hypothesis.py v1 sent position before ucinewgame and searched startpos; fixed, now has a guard.
- NO PREDICTION was written for job 3 (process failure, stated in REPORT_job3.md).

RUNNING NOW: nothing. No job is mid-run.

NEXT exact command when sent back (area 5 has no 4th job, so this is cycle (c) with the next seed):
  python3 forge-combo29/swarm/25/job1b/make_R.py forge-combo29/swarm/25/job1c/R3_2521.fens 2521 250
