## 2026-11-16T21:52:00Z — checkpoint push (owner window; findings deadline 22:30 UTC)

seat: 25
area: 5 (principal variations and scores)
seed: 2501
branch: for-fable-and-opus/swarm-25
folder: forge-combo29/swarm/25/

DONE, all pushed:
- STEP 1 seat 25; STEP 2 build + HONESTY (312866 / 862329 / 3024920 / 4865609 all match).
- JOB 1 (PV legality + mate scores): 553 depth-12 S14 searches. 0 illegal PVs, 10 mate scores, 1 WRONG.
  S-F1: 8/8/1p6/8/p3p3/8/2Kpk3/8 w reports `mate -12` at d12..16; plain minimax proves white is mated in
  EXACTLY 4 (not 3), and the engine itself says `mate -4` from d22. Wrong by 8 moves. S-F2: that score
  wanders -12 -> -9 -> -6 -> -5 -> -4. S-C1 CONFIRMS seat 06 S-F10 with a correction.
  Rule-1 plants: plant_illegal.txt 5/5, plant_mate.txt 5/5.
- JOB 2 (draw scores): 140 depth-10 searches. KvK/KNvK/KBvK 60/60 = 0 (correct); KNNvK 20/20 non-zero
  (correct); threefold 20/20 = 0 (correct, all verified genuine threefolds).
  S-F3: at halfmove clock 99 the engine reports cp 0 at EVERY depth and at `go nodes 50000`, on boards
  with 6-11 legal clock-resetting moves. Exact boundary: clock 98 = -112 cp, clock 99 = 0. Clock 100/101
  = 0 nodes. S-F4: `EvalRule50Damp` true/false, depths 1..30 and UseNNUE false all still give 0, so it is
  a hard-coded draw test firing one ply early, not the damped eval.
  S-F5 (severity): the clock-99 move is -40, -999 and -160 cp worse than the engine's own clock-0 move.
  My P6 prediction was KILLED by this (I predicted at most 5 of 20 zeros; 16 of 20 were zero).
- 19-F12 harness audit: my harness is SAFE (stdin open, read to bestmove -> 12 info lines, 56720 nodes).
  The pipelined go+quit pattern does fabricate `bestmove a2a3` with 0 info lines; I do not report it as
  mine. Evidence in check_19F12/.
- Measurement-integrity (seat 19 NaN warning): check_pv.py now EXITS 3 on empty input (it used to print a
  clean all-zero table); analyse_draw.py exits 3 on any unparsed score. Fixed one real bug of my own:
  rule50_hypothesis.py v1 sent `position fen` before `ucinewgame`, so it searched startpos and looked like
  "clock makes no difference"; corrected, and it now has a guard that exits 3 on a startpos-looking answer.

RUNNING NOW: nothing (last command finished).
NEXT exact command (job 3 of area 5: checkmated/stalemated roots under ASan+UBSan):
  mkdir -p ~/build/asan && cd ~/build/asan && cmake /agent/repos/base/forge-combo29 \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined" && make -j4
