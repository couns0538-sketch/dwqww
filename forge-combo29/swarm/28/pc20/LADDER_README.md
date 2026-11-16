# Why the 10 s clock loses a ply — the cause is the STOP, and the plan arithmetic is identical

Answer to the question left open by S-F25-REVISED. Three measurements, each with its own script.

## 1. The plan is identical on both builds (`prediction_plan.txt` predicted this)

Read from each exe's OWN `uci` answer, not from source — every plan input has the same default on base
and on PC r15:

| option | base default | PC r15 default |
|---|---|---|
| Move Overhead | 10 | 10 |
| TmSoftDivisor | 22 | 22 |
| TmIncrementPercent | 75 | 75 |
| TmHardPercent | 60 | 60 |
| TmHardSoftMultiple | 5 | 5 |

So with equal clocks the plan is one number on both builds. Computed exactly as
`include/forge/clock_plan.hpp` does for moves_to_go = 0:

| wtime | available | soft plan | hard plan |
|---|---|---|---|
| 3000 | 2990 | 135 ms | 675 ms |
| 10000 | 9990 | 454 ms | 2270 ms |

**This makes the lost ply an arithmetic consequence of WHERE the search stops, not of the budget it was
given.**

## 2. The achieved time differs, and so does the stop fraction (`plan_vs_achieved.log`)

40 positions per cell, Threads 1 on both builds, each on its own settings.

| wtime | plan soft | build | achieved median | last iteration time | median last depth | achieved/soft |
|---|---|---|---|---|---|---|
| 3000 | 135 | base | 106.9 | 105 | 16 | 0.79 |
| 3000 | 135 | PC20 | 119.8 | 119 | 16 | 0.89 |
| 10000 | 454 | base | 349.7 | 349 | 20 | **0.77** |
| 10000 | 454 | PC20 | 311.0 | 300 | 19 | **0.68** |

At the 10 s clock the PC build stops at 68 % of its own soft plan where base stops at 77 %, and reaches
depth 19 where base reaches 20. At 3 s there is no separation. The PC build is not slower per node and not
shallower per node (S-F25-REVISED); it simply stops sooner relative to the identical plan.

## 3. Where the stop lands in the iteration ladder (`ladder_base.txt`, `ladder_pc20.txt`)

24 positions at wtime 10000, the full (depth, cumulative ms) ladder of every search:

| build | median last depth | median last-iteration finish | median cost of the last iteration | median growth factor | finish as a fraction of soft |
|---|---|---|---|---|---|
| base | 20 | 376 ms | 92 ms | 1.35x | 0.83 |
| PC20 | 19 | 287 ms | 62 ms | 1.25x | **0.63** |

An iteration costs 1.25-1.35x the previous one here, so a stop point 89 ms earlier (376 -> 287) is enough
to drop one whole ply: the next iteration would need roughly 77-125 ms more to complete.

## What this is and is not

**It is:** a stop-point difference against an identical plan. The plan is one number and the difference is
not in it, so the cause is in the code that decides when to stop — where `FORGE_FIX_HARD_LIMIT_EMERGENCY`
lives. That is a fixable constant (a threshold or a percentage), not a search-quality property.

**It is not:** proof that the PC build is leaving budget it could legally use on EVERY such position. I
wrote `budget_left.py` to test exactly that, projecting each position's next-iteration finish from its own
observed growth. It classes 15 of 24 PC20 positions as "the next iteration would have fitted inside soft"
versus 10 of 24 on base — but **that projection is a heuristic**: an iteration's cost is not predictable
from the previous ratio alone (the data contains growth factors from 0.30x to 5.60x), so I present the row
counts as an indication, not as a count of wasted milliseconds. The robust facts are the two in sections 1
and 2: identical plan, 0.68 vs 0.77 stop fraction, one ply.

## For the owner in one line
On this machine the PC build spends about 68 % of its own soft budget at a 10 s clock where the base tree
spends 77 %, and that is worth a ply at depth 19-20; the budget itself is the same on both builds, so the
parameter to look at is the one that decides when to stop, not `TmSoftDivisor`.
