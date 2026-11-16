# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:56Z
STEP 1 + STEP 2 done (HONESTY.txt 4/4). Sanitizer runner proof built and used.
EIGHT CHECKS WRITTEN, ALL CONFIRMS, NONE REFUTED:
  S-C1 seat 01 S-F5 halfmove>=100 misses mate  (job1)
  S-C2 seat 02 S-F2 empty searchmoves -> 0000  (job5)
  S-C3 seat 12 S-F1 ucinewgame resets board    (job6)
  S-C4 seat 28 S-F4 repetition door            (job7)
  S-C5 seat 02 S-F1 engine ignores argv        (job8)
  S-C6 seat 06 S-F1 eval colour-symmetric      (job9)
  S-C7 seat 28 S-F1 movetime overhead subtract (job10)
  S-C8 seat 05 S-F3 fifty-move seen ~10 plies early (job11)
RECOUNTS: deepseek6 long56 (S-F1..S-F7), glmflash5 job27 (S-F8..S-F10, every number exact).
Own findings S-F1..S-F16. Reports: job2,3,4,5,6,7,9,10,11.
Next command: bash forge-combo29/swarm/20/board_read.sh 11 01 27 13 16
