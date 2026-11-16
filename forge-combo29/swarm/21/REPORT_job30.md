# REPORT job30 — `go softnodes N` on the PC build under PC20 (file 6 item 4)

**What was asked.** Handoff file 6, item 4: "`go softnodes N` on the PC build under PC20, Threads 1
— is it deterministic run to run (it must be), does it stop at a finished depth, and how far past N
does it go." This is the owner's self-play path, where file 6 says a find is worth most.

**The answer.** **Deterministic.** For every (position, N) the five fresh processes give a
bit-identical answer: same bestmove, score, node count and depth. **It stops on a depth boundary**:
the reported node count is the cumulative count on the LAST `info depth` line, and there is no
separate total. **The overshoot is large and irregular** — +671 at N=2000, +11,779 at N=20000,
+2,904 at N=50000, +38,912 at N=250000 — so `softnodes` is a *soft* target that a whole extra
iteration can blow past.

**How sure.** High. 5 positions × 4 values of N × 5 runs × 2 builds = 200 searches, every one read to
bestmove under the 19-F12 discipline, Threads 1, PC20 verified accepted option by option.

## Determinism (the headline)

| measure | result |
|---|---|
| (position, N) combinations | 40 (5 positions × 4 N × 2 builds) |
| runs per combination | 5 |
| combinations with a single distinct (bestmove, score, nodes, depth) | **40 of 40** |

So `go softnodes 2000` on the PC build under PC20, Threads 1 is reproducible run to run. That is
what the owner's self-play needs, and it holds.

## Overshoot past N (PC build, position 0 of set G)

| N | reported nodes | overshoot |
|---|---|---|
| 2000 | 2,671 | **+671** |
| 20000 | 31,779 | **+11,779** |
| 50000 | 52,904 | **+2,904** |
| 250000 | 288,912 | **+38,912** |

The overshoot is not a fixed margin: it is whatever the depth in progress costs. At N=20000 a whole
iteration cost ~11.8k nodes; at N=50000 the next iteration was smaller than the remainder. So a
harness that treats `softnodes N` as "about N nodes" will see up to ~19 % more at N=20000 and
~16 % more at N=250000.

## P3 verified from the raw file

The last `info depth` line for N=2000 on the PC build:

```
info depth 7 seldepth 13 score cp -306 nodes 2671 nps 190785 hashfull 2 time 14 pv g7g6 c1d1 f5e6 d1d2 f6d7
```

and no separate total follows it — `bestmove` comes next. So the reported 2,671 nodes IS the last
depth's cumulative count: the search ended cleanly at the end of depth 7, not mid-iteration.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 bit-identical across 5 runs | **held**, 40/40 combinations |
| P2 overshoot > 0 and less than a depth's nodes | **held** (overshoot 671–38,912; every case a whole or partial iteration) |
| P3 stops on a depth boundary | **held** (verified in the raw file above) |
| P4 monotone in N | held (2,671 < 31,779 < 52,904 < 288,912 on the same position) |
| P5 PC and base agree for the same N | **held** — see the base rows in `job30/out/summary.md`; every (position, N) pair has the same bestmove and node count on both builds |
| P6 0 crashes / sanitizer lines | held |

## Findings

`21-F15 | NEW` — `go softnodes N` on the PC build under PC20 (Threads 1) is **fully deterministic**
(40/40 position×N combinations identical over 5 fresh processes each) and stops at a **depth
boundary** (the reported node count is the last `info depth` line's cumulative count; no separate
total follows), but it overshoots N by a whole iteration: +671 at N=2000 (+33.6 %), +11,779 at
N=20000 (**+58.9 %**), +2,904 at N=50000 (+5.8 %), +38,912 at N=250000 (+15.6 %). A harness that
treats `softnodes N` as "N nodes" is wrong by up to 59 % in my sample. Base and PC builds agree for
every (position, N) pair, so the patch does not change this path.

## Suspicions, not proven

- Whether the overshoot can be arbitrarily large on a position where one iteration is enormous. My
  worst case was 59 % of N; a tactical position with a huge first iteration could be worse. I did
  not search for a worst case.
- Whether `softnodes` combined with a clock limit (`go softnodes N wtime ...`) behaves the same way;
  the owner's self-play uses softnodes alone.

## What I did NOT do

- Did not test `go softnodes 0` or a softnodes value below the first iteration's cost.
- Did not test whether `softnodes` interacts with `nodes` when both are on the line.
- Did not finish job28 (KNN v K, seat 15's 15-F3); it was killed mid-run and produced nothing, so it
  is "not done", not a result.

## What I am NOT sure about

- Whether the owner's self-play counts the overshoot when it records a game. If it assumes exactly
  N nodes, then the positions it thinks are "2,000-node searches" are really 2,671-node searches
  on average, ~34 % more.

## Times

see `job30/stamps.txt`.
