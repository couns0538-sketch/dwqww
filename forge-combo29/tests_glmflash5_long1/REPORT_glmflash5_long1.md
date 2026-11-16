# REPORT glmflash5 long 1 — the control: nodes 20000 vs nodes 10000

1. The control: S14 on both sides, the only difference is the node count (20,000 vs 10,000). 150 games, 75 pairs.
2. W-L-D: 87-13-50 (the 20,000-node side). Pentanomial [0, 2, 18, 34, 21].
3. Elo: +187.77 [-146.30, -229.24 from the base's perspective] ± 41.47 — about +188, the expected ~+200 ✓.
4. One seed. The infrastructure is VALIDATED: the higher-node side wins decisively.

The first attempt accidentally used `-each nodes=20000` (both engines at 20,000) giving [0, 0, 75, 0, 0] —
all pairs perfectly balanced. Fixed to per-engine node counts. The corrected run above is the real control.

Games by ending: not tracked per game (fastchess's PGN); the pentanomial shows a normal distribution for
a 200-Elo advantage.

times: see stamps.txt.
