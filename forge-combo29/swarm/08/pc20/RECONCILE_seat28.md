# RECONCILIATION with seat 28 on the owner's 6 s + 0.06 clock — seat 08

## The short answer: seat 28 is right and my 3-position sample was too narrow. The tail is POSITION-DEPENDENT.

| | seat 28 | me (before) | me (after) |
|---|---|---|---|
| positions | 60 per build | **3** | their outliers + 19 shaped boards |
| median | 226.3 ms | 295.2 ms | — |
| p99 | 1499.3 ms | 457.4 ms | — |
| worst | **1585.3 ms** | **482.4 ms** | **1585.4 ms** |
| searches over 1.2 s | 5 of 120 | **0 of 240** | reproduced |

**I ran their exact outlier boards on my own harness at the same control and they reproduce** (`reconcile_s28.txt`,
3 fresh processes each, PC r15, PC20, Threads 1, Hash 16, `go wtime 6000 btime 6000 winc 60 binc 60`):

| their board | seat 28 measured | my median | my worst | verdict |
|---|---|---|---|---|
| `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b` | 1585.3 ms | **1585.4 ms** | 1585.8 ms | **reproduced to 0.1 ms** |
| `7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b` | 1439.5 ms | 813.8 ms | 1585.9 ms | reproduced on one of three runs |
| `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w` | 834.7 ms | 985.0 ms | 990.1 ms | same order, 18 % higher |
| `8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b` | 804.9 ms | 834.9 ms | 876.1 ms | reproduced |
| `1r6/…/R1R5 b` (their ordinary) | 160.7 ms | 178.8 ms | 214.9 ms | reproduced |
| `8/3k1p2/1R4pp/4P3/5KP1/5P2/8/r7 w` | 204.2 ms | 220.1 ms | 220.6 ms | reproduced |

My worst on their boards: **1585.9 ms**. So the two harnesses agree; only the position sets differed.

**Why:** my three boards were `startpos` and two full-material middlegames — the two FASTEST classes. Their 60
positions came from real games and included endgames. I sampled one end of the distribution and reported it as the
distribution. That is the same error as my earlier ten-run threading read, in a different guise: **a small sample
presented as a population.** 08-N1 ("a summary I typed is not evidence") needs a companion: a three-position median
is not a population median.

## The position-dependence, measured (the version the owner needs)

`tail_by_shape.txt` — four shape classes, 5 positions each, same control, Threads 1:

| class | n | median wall | worst | median depth | median last-iteration cost |
|---|---|---|---|---|---|
| **few pieces, few moves** | 5 | **853.1 ms** | **1585.4 ms** | 17 | **415.4 ms** |
| few pieces, many moves | 4 | 388.9 ms | 852.3 ms | 20 | 201.6 ms |
| full material, few moves | 5 | 386.2 ms | 660.8 ms | 19 | 165.5 ms |
| **full material, many moves** | 5 | **161.2 ms** | 398.5 ms | 17 | **57.1 ms** |

**A 5.3x spread in median wall time across position classes, on the same clock and settings.** The driver is
visible in the last column: the cost of ONE iteration is 415 ms in a sparse endgame and 57 ms in a busy middlegame.
The engine stops at the end of whatever iteration it is in (08-F10), so a position whose iterations are expensive
overshoots the 317 ms soft plan by 3-5x, and one whose iterations are cheap lands close to it.

**What blows the tail:** sparse positions — very few pieces AND few legal moves — where each extra depth costs a
large multiple of the last. That is the shape of the boards seat 28 caught: 7 pieces / 5 legal moves, 12 pieces /
6 moves, 9 pieces / 13 moves.
**What does not:** full-material middlegames with 30-50 legal moves, which is what I had sampled.

## The reconciled finding for the owner

On the owner's real clock, the worst single move is **not** 482 ms as I first reported; it is **~1.59 seconds,
= exactly the engine's own 1585 ms hard plan**, and it happens in sparse endgames. In 120 searches seat 28 measured
5 over 1.2 s; I reproduce that class of board and the exact worst case. **The engine still never exceeded the
six-second clock** (0 over in their 120 and in my 240), so this is a heavy tail that eats 20-26 % of the clock in one
move, not a lost-on-time risk.

## What I cannot settle, stated
- Whether seat 28's 5-of-120 rate holds on a larger random sample: I tested their 4 outliers plus 19 shaped boards,
  not 120 fresh game positions. My class medians (853 ms for the sparse class) support a frequent heavy tail, but
  a frequency claim needs their sample size or larger.
- Their board #2 gave me 813.8 ms median against their 1439.5, with one of my three runs at 1585.9 — so that board is
  bimodal on my harness too, and a single-run comparison on it is meaningless. Stated rather than averaged away.

## Show it again
    cd forge-combo29/swarm/08/pc20 && python3 reconcile_s28.py /tmp/r28.txt
    cd forge-combo29/swarm/08/pc20 && python3 tail_by_shape.py /tmp/ts.txt
