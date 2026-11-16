# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:56Z — SESSION SUMMARY (all pushed; see FINAL_REPORT.md)
(the previous block's header read 22:00Z; I corrected it to the real `date -u` value 21:53Z. The container clock has
been advancing abnormally slowly this session, so I pushed at every job boundary instead of trusting it.)

STEP 1 + STEP 2 done (HONESTY.txt 4/4 pins). Sanitizer runner proof built (planted fault 3 lines / real 0).

### AUDITS (all three broadcasts answered, folder AUDIT/)
- **19-F12** fabricated bestmove on mid-search quit: every harness audited; valid ones wait for `bestmove`;
  two already-discarded scripts named; new driver `AUDIT/hardened.py`. Re-verified startpos depth 12 = e2e4, 56,720.
- **silent-parse** (seat 19 warning 2): 7 parsing checkers fed a silent fake engine -> ALL hung, none printed a
  verdict. No silent-parse defect; noted that hanging is weaker than failing loudly.
- **seat 10 warm/cold**: `Clear Hash` never used; every node count from a fresh process; 56,720 x3.

### CHECKS: 15 written, ALL CONFIRMS, none REFUTED (two carry corrections to the finding)
S-C1 seat01 S-F5 | S-C2 seat02 S-F2 | S-C3 seat12 S-F1 | S-C4 seat28 S-F4 | S-C5 seat02 S-F1
S-C6 seat06 S-F1 | S-C7 seat28 S-F1 | S-C8 seat05 S-F3 | S-C9 seat05+seat25 S-F1 (S14-conditional)
S-C10 seat27 S-F3 (hashfull 1000-cluster window; nodes identical 87,135)
S-C11 seat17 S-F1 (0000 on a live board; + the 64-info-line detail)
S-C12 seat17 S-F3 (bench pins immune to history drift: 862329 x3)
S-C13 seat06 S-F6 (search not colour-symmetric: 18/20 scores differ; my rate 10% vs their 28.6%)
S-C14 seat28 S-F5 (increment ignored at tiny clocks; CORRECTED threshold 13/14, not 10/11)
S-C15 seat28 S-F7 (wtime 0 answers legally, 0 hangs in 20)
RECOUNTS: deepseek6 long56, glmflash5 job27 (every number exact).

### FINDINGS
S-F1..S-F26. S-F21 WITHDRAWN by me (no forced mate existed). Headline own results:
S-F13 seat 01's patch fixes the halfmove door but NOT the repetition door (proved on a rebuilt patched binary);
S-F22 true mate distance on the S-F19 board is 8 plies, proved both ways with a verified line;
S-F18/S-F19 only 3 of 14 S14 options break mate reporting, and LmpBase=8 loses the mate at depth 12;
S-F16 two different cp-0 mechanisms (0 nodes vs millions); S-F26 increment boundary = Move Overhead + ~4;
S-F27 UCI cannot reveal the tie-break order (a limit on how such findings can be made at all);
S-F28 FABLE_TO_swarm_3 read: the drawn-root defect is BASE-TREE ONLY and repaired on the PC since 15 Nov;
S-F30 planting Rule-1 controls exposed a crash/hang mislabel in my own fuzz classifier (fixed; total unchanged).
FINAL_REPORT.md holds the full session summary; FABLE_NOTES.md the Opus file read + Rule-1 table.

Next command: `cd /agent/repos/dwqww && bash forge-combo29/swarm/20/board_read.sh 01 06 27 28`
