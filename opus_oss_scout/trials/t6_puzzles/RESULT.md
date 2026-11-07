# T6 Lichess puzzles as a fixed-node tactical screen - RESULT

Data: Lichess puzzles (CC0-1.0), 2,000 sampled with seed 20261106 (ratings 399-3025, median 1400). Engine: the lock
exe trial_w6 (4181a589), OwnBook false, Hash 16, Threads 1. Commands: CMDS.md; raw output `logs/t6_solve.txt`, details
and the first 30 misses per budget in `t6_result.json`. Run 21:36-21:39 (PC clock), Idle on CPUs 2-3, after T1b.

| Rating band | Puzzles | Solved at 20k nodes | Solved at 200k nodes |
|---|---|---|---|
| 0-999 | 476 | 474 (99.6 %) | 475 (99.8 %) |
| 1000-1499 | 624 | 619 (99.2 %) | 624 (100.0 %) |
| 1500-1999 | 516 | 499 (96.7 %) | 513 (99.4 %) |
| 2000-2499 | 301 | 267 (88.7 %) | 293 (97.3 %) |
| 2500+ | 83 | 61 (73.5 %) | 72 (86.7 %) |
| **All** | **2,000** | **1,920 (96.0 %), 21 s** | **1,977 (98.8 %), 166 s** |
| mate themes | 633 | 632 | 632 |

## Reading
- The screen works end to end (CC0 data via a public API, no parquet tools, stdlib Python, ~10 ms per puzzle at 20k
  nodes).
- Fixed nodes + Threads 1 + ucinewgame per puzzle make every answer reproducible and independent of the CPU load.
- **Sensitivity sits in the 2000+ bands.** Below 2000 the lock is near 100 %, so those puzzles carry almost no
  information.
  - A useful screen samples only rated >= 2000 (or >= 2200) puzzles at 20k-50k nodes.
  - With ~1,000 such puzzles, a paired lock-vs-candidate comparison takes ~1 min per side.
- The first-move rule slightly under-counts: other mates in one are also correct on Lichess. The one mate-theme miss
  is in `t6_result.json`.
- No Elo claim: puzzle rates are a tactical regression check, and the gate decides.
