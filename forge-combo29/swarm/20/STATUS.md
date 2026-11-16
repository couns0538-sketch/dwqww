# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T22:00Z — pre-22:05 checkpoint

STEP 1 + STEP 2 done (HONESTY.txt 4/4 pins). Sanitizer runner proof built (planted fault 3 lines / real 0).

### AUDITS (all three broadcasts answered, folder AUDIT/)
- **19-F12** fabricated bestmove on mid-search quit: every harness audited; valid ones wait for `bestmove`;
  two already-discarded scripts named; new driver `AUDIT/hardened.py`. Re-verified startpos depth 12 = e2e4, 56,720.
- **silent-parse** (seat 19 warning 2): 7 parsing checkers fed a silent fake engine -> ALL hung, none printed a
  verdict. No silent-parse defect; noted that hanging is weaker than failing loudly.
- **seat 10 warm/cold**: `Clear Hash` never used; every node count from a fresh process; 56,720 x3.

### CHECKS: 12 written, ALL CONFIRMS, none REFUTED
S-C1 seat01 S-F5 | S-C2 seat02 S-F2 | S-C3 seat12 S-F1 | S-C4 seat28 S-F4 | S-C5 seat02 S-F1
S-C6 seat06 S-F1 | S-C7 seat28 S-F1 | S-C8 seat05 S-F3 | S-C9 seat05+seat25 S-F1 (S14-conditional)
S-C10 seat27 S-F3 (hashfull 1000-cluster window; nodes identical 87,135)
S-C11 seat17 S-F1 (0000 on a live board; + the 64-info-line detail)
S-C12 seat17 S-F3 (bench pins immune to history drift: 862329 x3)
RECOUNTS: deepseek6 long56, glmflash5 job27 (every number exact).

### FINDINGS
S-F1..S-F20 live; S-F21 WITHDRAWN (my error); S-F22 true mate distance = 8 plies (proved both ways);
S-F23 my own discarded mate scripts recorded; S-F24 node-count audit statement.

Next command: `cd /agent/repos/dwqww && bash forge-combo29/swarm/20/board_read.sh 01 06 27 28`
