# REPORT — seat 07, job 46: refutation of seat 27's S-F12 ("the clock is ignored when Black is to move")

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 27's S-F12 claims a live defect on the owner's match path — that `go wtime N`
ignores the clock entirely when Black is to move, searching the same tree for every N including `wtime 0`.
Nobody had checked it. It is the most serious unverified claim on the board.

**Answer:** **it does not reproduce — on either build.** On the reported FEN with Black to move, the tree
grows from **39 nodes at `wtime 0` to 178,324 at `wtime 3000`** on the PC build, and the bestmove changes
from `e7c8` to `f1g1`.

**How sure:** high. Controls prove the harness can tell a short search from a long one, every cell was
reproduced on a second run, and I found a concrete explanation for the number seat 27 quoted.

## The measurement (PC r15 under PC20, Threads 1, Hash 16, fresh process per cell, wall clock timed)

Their FEN: `2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55`, **Black to move**.

| `go wtime N btime N` | wall | depth lines | nodes | score | bestmove |
|---|---|---|---|---|---|
| 0 | 1.2 ms | 1 | **39** | cp −55 | `e7c8` |
| 1 | 1.1 ms | 1 | 39 | cp −55 | `e7c8` |
| 3 | 0.8 ms | 1 | 39 | cp −55 | `e7c8` |
| 10 | 1.1 ms | 1 | 39 | cp −55 | `e7c8` |
| 50 | 1.4 ms | 6 | **918** | cp −46 | **`f1g1`** |
| 200 | 7.0 ms | 10 | **11,488** | cp −21 | `f1g1` |
| 1000 | 27.8 ms | 18 | **53,919** | cp 0 | `f1g1` |
| 3000 | 90.3 ms | 22 | **178,324** | cp 0 | `f1g1` |

**The tree grows by four orders of magnitude and the move changes.** The clock is honoured.

Their claim was that **every** N gives "depth 20, 286,156 nodes, ~124 ms". Mine gives that for none.

## Controls (required before the refutation means anything)

| control | result |
|---|---|
| `go movetime 5` must be short | **1.3 ms, 497 nodes, 5 depth lines** — yes |
| `go movetime 3000` must be much longer | **2,990.8 ms, 4,306,146 nodes, 36 lines** — yes |

So the harness distinguishes a 1 ms search from a 3 s search by three orders of magnitude in nodes. A
"clock ignored" result found with this harness would be real; it was not found.

## The discriminator seat 27 named, checked as they framed it

They said the side to move is the discriminator: same board with `w` to move gives the emergency path,
with `b` to move the same tree. On their FEN with **White** to move I get **21 nodes / 1 line at
`wtime 0`** and **87,091 nodes / 16 lines at `wtime 2000`** — so White also scales. Both sides honour the
clock; the side to move is not a discriminator.

## A second board of my own, Black to move

Not one position's quirk: `r1bq1rk1/.../R2QKB1R b KQ - 0 8` gives **82 nodes at `wtime 0`**, 654 at
`wtime 50`, and **202,779 at `wtime 3000`**. Scaling again.

## The likely source of their figure

Their quoted answer — **286,156 nodes, depth 20, ~124 ms** — is **exactly** what I measure on the
**BASE build** at `wtime 3000`:

| build | `wtime 0` | `wtime 3000` |
|---|---|---|
| PC r15 / PC20 | 39 nodes | 178,324 nodes (22 lines) |
| **base / none** | 39 nodes | **286,156 nodes (20 lines, 120 ms)** |

Reproduced identically twice on each build. So that number very plausibly came from the base build, or
from S14 rather than PC20, and was then read as "the value the PC build returns for every budget". Their
observation that the number did not change may have been an artefact of how the cells were collected.

**I could not reproduce "clock ignored" on either build** — the base build scales too (39 → 286,156).

## Findings

**07-C45** in FINDINGS.md.

## Suspicions, not proven

- What exactly produced their constant reading. My best hypothesis is a mix-up between builds or regimes,
  supported by the exact node-count match, but I cannot see their harness and will not assert a mechanism
  beyond that.

## What I did NOT do

- Did not read their raw files (they named `job7`-style outputs in another row; the S-F12 row cites a
  board and a result, not a path I could run). My brief is to use my own harness, which is what makes
  this an independent check.
- Did not test `go btime` alone or asymmetric clocks; their claim was about `wtime` with the side to move,
  which is what I tested as framed.

## What I am NOT sure about

- Whether some *other* input (e.g. a clock below the 10 ms Move Overhead with Black to move) does hit an
  emergency path in a way their claim gestures at. At `wtime 0/1/3/10` I see the 1-line 39-node emergency
  answer, which is correct behaviour, not a defect.

## Times

See job46/stamps.txt.
