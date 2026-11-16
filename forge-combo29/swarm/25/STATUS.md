## 2026-11-16T21:36:00Z — checkpoint push (owner window until 22:35 UTC)

seat: 25
area: 5 (principal variations and scores)
seed: 2501
branch: for-fable-and-opus/swarm-25
folder: forge-combo29/swarm/25/

Done:
- STEP 1 seat 25 claimed; STEP 2 build + HONESTY all four numbers match (HONESTY.txt).
- AREA 5 job 1 DONE: 553 depth-12 S14 searches (O 200 + G 353). 0 illegal PVs; 10 mate scores;
  9 correct, 1 WRONG (S-F1). Rule 1 plants both run through the same harness (plant_illegal.txt 5/5,
  plant_mate.txt 5/5). Determinism: 0/200 differ ignoring nps/time/hashfull.
- S-F1 proven: 8/8/1p6/8/p3p3/8/2Kpk3/8 w says `mate -12` at d12..16 but plain minimax proves white is
  mated in EXACTLY 4 (and not 3); engine's own d22+ answer is correctly `mate -4`. Wrong by 8 moves.
- S-C1 CONFIRMS seat 06 S-F10 (depth-10 result reproduces: 6 mate scores, 0 wrong) with the correction
  that "mate machinery sound" does not generalise to depth 12.
- 19-F12 HARNESS AUDIT (coordinator broadcast) DONE: my harness is SAFE. My pattern (stdin open, read
  until bestmove) gives 12 info lines / 56720 nodes / e2e4; the pipelined go+quit pattern gives
  bestmove a2a3 with 0 info lines. quit mid-running-search is also safe (1391723 nodes at d19).
  No recorded result of mine used the fabricating pattern. Evidence: check_19F12/.

Running now:
- AREA 5 job 2 (draw scores): A/B/C/D/F position sets built (20 each). The E group (threefold by move
  list) is still being generated; the first two generators found 3 then 0 distinct games — being fixed.

Next exact command:
  python3 forge-combo29/swarm/25/job2/make_draw_sets.py forge-combo29/swarm/25/job2 2501
then run the depth-10 draw-score harness over A..F.
