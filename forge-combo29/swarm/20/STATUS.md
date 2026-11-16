# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:42Z
STEP 1 + STEP 2 done (HONESTY.txt 4/4 pins). Sanitizer runner proof built (planted fault 3 lines / real 0).
CHECKS WRITTEN (all CONFIRMS, no REFUTES yet):
  S-C1 seat 01 S-F5 (halfmove>=100 misses mate in 1) - job1/CHECK_s01F5.md
  S-C2 seat 02 S-F2 (empty searchmoves -> bestmove 0000) - job5/CHECK_s02F2.md
  S-C3 seat 12 S-F1 (ucinewgame resets the board) - job6/CHECK_s12F1.md
  S-C4 seat 28 S-F4 (repetition door) + S-F13 (seat01's patch is NOT sufficient) - job7/CHECK_s28F4.md
  S-C5 seat 02 S-F1 (engine ignores argv) - job8/CHECK_s02F1.md
  S-C6 seat 06 S-F1 (eval colour-symmetric) + S-F14 (sign-convention trap) - job9/CHECK_s06F1.md
RECOUNTS: deepseek6 long56 (S-F1..S-F7), glmflash5 job27 (S-F8..S-F10, every number exact).
Own findings: S-F1..S-F14. Reports: job2, job3, job4, job5, job6, job7, job9.
Next command: bash forge-combo29/swarm/20/board_read.sh 01 28 06 12 02 11 21
