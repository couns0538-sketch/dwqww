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
