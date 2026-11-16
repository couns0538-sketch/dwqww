# The clock tail — p90 and the arithmetic the owner can re-run

30 self-play games, **3,834 searches**, PC r15, PC20, **Threads 1**, Hash 16, clock **6000 ms + 60 ms**.
Data: `games30.jsonl`. Stats: `tail_stats.txt`.

## The per-move distribution

| | per-move search time |
|---|---|
| min | 0 ms |
| p10 | 50 ms |
| p25 | 67 ms |
| **median** | **104 ms** |
| p75 | 170 ms |
| **p90** | **269 ms** |
| p95 | 368 ms |
| p99 | 564 ms |
| max | **1,293 ms** |
| mean | 139.3 ms |

**80.3 % of all moves take longer than the 60 ms increment.** 51.8 % take longer than 100 ms.

## The arithmetic — recomputable for any control

A clock search is **negative-sum** when the per-move search time exceeds the increment. The moves a
clock of `B` ms survives is:

> **moves until empty = B / (search_time − increment)**

| basis | search time | net drain/move | moves of one side from 6,000 ms |
|---|---|---|---|
| median | 104 ms | 44 ms | **136** |
| **p90** | **269 ms** | **209 ms** | **29** |
| mean | 139.3 ms | 79.3 ms | **76** |

So the answer depends entirely on which statistic you believe applies — and **the tail is what decides
it**. At the median the clock survives 136 moves; at p90 only **29**. The observed minimum clock was
**115 ms after 160 plies** (game 13), which sits between those extremes: the games did not run at p90
throughout, but they came close to the p90 rate in their expensive middlegame phase.

## Sizing an increment that survives a bad stretch

> - **≥ 269 ms** covers the p90 move
> - **≥ 368 ms** covers the p95 move
> - **≥ 1,293 ms** covers every move observed

**60 ms is below the median, so the control is negative-sum on more than half of all moves.** To be
safe against a bad stretch (a run of p90 moves) the increment would need to be roughly **270 ms**, more
than **four times** the current setting.

## Honest construction of this number

For anyone checking: the p90 comes from **3,834 searches over 30 games**. My first pass at this number
used only the 6-game 400-ply run (843 searches, p90 258 ms) because the 30-game file had been overwritten
by the 6-game run's default output name. I re-ran the 30 games into `games30.jsonl` and these are those
figures. The p90 moved only from 258 to 269 ms with 4.5× the data, so it is stable — but the reported
number is the 3,834-search one, and `games.jsonl` now holds the 6-game set with a different name.
