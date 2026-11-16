# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:53Z — deadline 22:30 noted; everything below is already pushed

STEP 1 + STEP 2 done (HONESTY.txt 4/4 pins). Sanitizer runner proof built (planted fault 3 lines / real 0).

### THREE BROADCAST AUDITS, ALL COMPLETE (folder AUDIT/)
1. **19-F12 (fabricated bestmove on mid-search quit):** audited every harness. Valid ones wait for `bestmove`
   before `quit`. Two were already discarded before the broadcast (`job3/out/fallback.out.txt`, `job2/quitcut.sh`).
   New driver `AUDIT/hardened.py`. Re-verified: startpos depth 12 -> e2e4, cp 30, **56,720 nodes**.
2. **Silent-parse verdicts:** fed every parsing checker a FAKE engine that answers uciok then nothing.
   **All 7 hung; none printed a verdict.** No silent-parse defect, but I record that hanging is weaker than failing
   loudly (`AUDIT/AUDIT.md`).
3. **Seat 10's warm/cold node warning:** `Clear Hash` is used NOWHERE in my work (grep: no matches); every node count
   of mine comes from a fresh process per search; three fresh runs of startpos depth 12 give 56,720 three times.
   No table of mine compares warm searches, so nothing needs a "warm" label (`AUDIT/AUDIT_node_counts.md`).

### CHECKS (9, all CONFIRMS, none REFUTED)
S-C1 seat01 S-F5 | S-C2 seat02 S-F2 | S-C3 seat12 S-F1 | S-C4 seat28 S-F4 | S-C5 seat02 S-F1
S-C6 seat06 S-F1 | S-C7 seat28 S-F1 | S-C8 seat05 S-F3 | S-C9 seat05+seat25 S-F1 (S14-conditional)
RECOUNTS: deepseek6 long56 (S-F1..S-F10); glmflash5 job27 (every number exact).

### FINDINGS
S-F1..S-F20 live. **S-F21 WITHDRAWN** (my error). New: **S-F22** true mate distance on the S-F19 board is exactly
8 plies (`mate -4`), proved by an exact predicate both ways plus an exhibited 8-ply line ending in verified
checkmate — the engine's depth-12 `mate -7` overstates it by 6 plies. **S-F23** records two of my own job16 scripts
whose mate "distance" no line realised; both discarded, no number recorded.

Next command: `cd /agent/repos/dwqww && bash forge-combo29/swarm/20/board_read.sh 01 05 19 28`
