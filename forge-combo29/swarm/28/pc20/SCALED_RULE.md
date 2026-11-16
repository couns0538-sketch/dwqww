# Bounding the sparse-endgame tail with a soft-scaled stop rule: the arithmetic, and what it costs

Arithmetic on data I already measured — no new experiment. Question: for the heavy class, what would a stop
rule cheaper than the hard limit buy, and how many plies would it cost?

## The rule under test

Today (S-F31) a search can run far past its last completed iteration to the hard limit and finish nothing.
The candidate rule is the textbook one:

> before starting an iteration, if `elapsed + expected_cost_of_next > budget`, stop.

I evaluate it with `budget = soft` — the plan's own soft limit — using the measured iteration ladders. The
"saving" is `actual last-completion time − the last completion at or before soft`; the "ply cost" is the
depth difference. Both come straight from the recorded (depth, cumulative ms) ladders.

## The class split
From my cross-build runs on the outliers (all at a constant 6000 ms clock):

| position | found on | base wall ms | PC20 wall ms |
|---|---|---|---|
| base#7 `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w` | base | 1585 | 843 |
| base#20 `8/8/4K1k1/8/4N1P1/8/1b6/8 w` | base | 1298 | 210 |
| base#28 `8/p7/5pk1/7p/r2NKP2/4P1P1/PR5P/8 b` | base | 1252 | 250 |
| pc#37 `7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b` | PC20 | 971 | 1562 |
| pc#57 `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b` | PC20 | 281 | 1586 |

**This is worth flagging separately from the tail question:** the heavy searches are not a property of the
position alone. `base#7` costs 1585 ms on the base build and 843 ms on PC20; `pc#57` costs 281 ms on base
and 1586 ms on PC20. The same board is heavy on one build and cheap on the other. So "sparse endgames are
the risk class" is true, but the specific board that blows up differs by build — which is consistent with
S-F27's finding that the switch set changes the tree.

## The arithmetic (ladders at wtime 10000, soft 454 ms)

| build | n | saving median | saving mean | saving max | plies lost median | mean | max | lose 0 plies | lose 1 | lose 2+ |
|---|---|---|---|---|---|---|---|---|---|---|
| base | 24 | 0 ms | 190 ms | 1239 ms | 0 | 0.58 | 3 | 15 | 5 | 4 |
| PC20 | 24 | 0 ms | 108 ms | 826 ms | 0 | 0.42 | 3 | 18 | 3 | 3 |

The six largest opportunities:

| build | index | saving | plies lost | actual time | actual depth |
|---|---|---|---|---|---|
| base | 21 | 1239 ms | 1 | 1287 ms | 30 |
| base | 8 | 732 ms | 1 | 1013 ms | 19 |
| base | 4 | 533 ms | 1 | 703 ms | 22 |
| base | 23 | 516 ms | 2 | 891 ms | 20 |
| base | 15 | 504 ms | 3 | 829 ms | 20 |
| base | 11 | 487 ms | 2 | 680 ms | 21 |
| PC20 | 16 | 826 ms | 2 | 1225 ms | 18 |
| PC20 | 8 | 584 ms | 1 | 830 ms | 18 |
| PC20 | 1 | 426 ms | 3 | 838 ms | 23 |
| PC20 | 23 | 323 ms | 2 | 777 ms | 22 |
| PC20 | 4 | 307 ms | 1 | 717 ms | 19 |
| PC20 | 15 | 122 ms | 1 | 467 ms | 19 |

## What the owner can act on

1. **For most positions the rule costs nothing.** 15 of 24 (base) and 18 of 24 (PC20) lose **zero** plies,
   because their last completed iteration already fell inside soft. The rule only bites on the tail.
2. **On the tail it buys 300-1240 ms for 1-3 plies.** Every one of the twelve largest opportunities in the
   table costs 1-3 plies. The single biggest (base idx 21, 1239 ms saved) costs **1 ply**.
3. **A cheap refinement worth naming:** the searches that cost 2-3 plies are the ones where the saved time
   is small relative to the ply (base idx 15: 504 ms for 3 plies). A rule that only refuses an iteration
   when the projected overshoot exceeds, say, 2x the last iteration cost would keep the 1-ply wins and skip
   the 3-ply ones. I have not measured that variant — it is a suggestion, not a result.
4. **Scale caveat, stated plainly:** these ladders are at `wtime 10000` (soft 454), not the owner's 6 s
   (soft 317). The per-iteration costs do not transfer directly; the RATIOS above do approximately. I did
   not re-record 6 s ladders, so the ms figures in the tables are for the 10 s plan.

## What this does NOT establish
- It does not prove the rule is an improvement in playing strength. Saving time is good, losing plies is
  bad, and only a match settles the exchange rate. What this file gives is the quantity: **~300-1200 ms of
  a 10 s budget recovered for 1-3 plies on the heavy searches, and free on the other two thirds.**
- It is not a measurement of the 6 s control. The class split and the wall times in the first table are
  from 6 s runs; the per-iteration arithmetic is from 10 s ladders.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 scaled_rule.py
```
Raw: `scaled_rule_out.txt`, `ladder_base_w10000.tsv`, `ladder_PC20_w10000.tsv`, `out_cd/constant_6000.tsv`.
