# `go softnodes N` on the PC build under PC20, Threads 1: deterministic, stops at a finished depth, overshoots 1.0-2.0x

FABLE_TO_swarm_6 item 4. This is the owner's self-play control (`go softnodes 2000`) and its match controls
(20000, 50000, 250000).

## Answers to the three questions asked
1. **Is it deterministic run to run?** **YES at every N**, on all three positions, five repeats each. Same
   final node count, same final depth, same move every time.
2. **Does it stop at a finished depth?** **YES at every N** — the final node count always equals a node
   count the engine itself reported for a depth, never a truncated in-between value.
3. **How far past N does it go?** Between **1.02x and 1.99x**, and the ratio grows with N.

## The table — pasted output (`softnodes.log`)

| N | position | final nodes | final/N | final depth | bestmove | stops at a depth boundary |
|---|---|---|---|---|---|---|
| 2000 | #1 | 2048 | 1.02 | 7 | f1e2 | yes |
| 2000 | #2 | 2208 | 1.10 | 7 | f1c4 | yes |
| 2000 | #3 | 3174 | 1.59 | 8 | e5d4 | yes |
| 20000 | #1 | 21812 | 1.09 | 12 | f1e2 | yes |
| 20000 | #2 | 26844 | 1.34 | 12 | f1c4 | yes |
| 20000 | #3 | 20748 | 1.04 | 11 | e5d4 | yes |
| 50000 | #1 | 56616 | 1.13 | 14 | f1e2 | yes |
| 50000 | #2 | 76559 | 1.53 | 15 | f1c4 | yes |
| 50000 | #3 | 63440 | 1.27 | 14 | e5d4 | yes |
| 250000 | #1 | 309981 | 1.24 | 18 | f1e2 | yes |
| 250000 | #2 | 498518 | 1.99 | 18 | f1c4 | yes |
| 250000 | #3 | 422654 | 1.69 | 18 | e5d4 | yes |

Summarised:

| N | deterministic across repeats (all positions) | final/N min..max | final depth range |
|---|---|---|---|
| 2000 | YES | 1.02..1.59 | 7..8 |
| 20000 | YES | 1.04..1.34 | 11..12 |
| 50000 | YES | 1.13..1.53 | 14..15 |
| 250000 | YES | 1.24..1.99 | 18..18 |

## What is worth the owner's attention
- **The overshoot is bounded by one iteration, as designed**, and that is exactly what makes it
  deterministic: the engine finishes the iteration that crosses N and stops. At `softnodes 2000` that means
  2,048-3,174 nodes, i.e. the owner's "first depth after 2,000 nodes" is literally true.
- **The ratio grows with N** (1.02-1.59 at 2k, 1.24-1.99 at 250k). That is the expected consequence of
  iterations getting relatively longer at higher N, and it means a 250k softnodes search can consume up to
  twice the stated budget in nodes. If any match control assumes `softnodes N` is a hard 250k, it is not.
- **The 4N hard cap never fired** (a 250k search would need 1,000,000 nodes to reach it; the largest here is
  498,518). So the cap is a backstop, not an operating limit.
- Every one of the twelve cells used `Threads 1`, `Hash 16`, PC20's full switch set, `ucinewgame` before
  each search — and S-F15 established that this process regime is bit-identical to a fresh process.

## Prediction score
Z1 (above N) SURVIVES. Z2 (1.0-1.5) **KILLED** — the max is 1.99 at 250k. Z3 (finished depth) SURVIVES.
Z4 (deterministic) SURVIVES. Z5 (under 4N) SURVIVES. Z6 (same shape at larger N) SURVIVES, though the
overshoot grows rather than staying flat. Z7 (depth monotone in N) SURVIVES: 7-8, 11-12, 14-15, 18.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 softnodes.py ~/build/r15-pc/forge /tmp/sn 3 5
```
Raw: `out_sn/softnodes.tsv` (includes the full per-depth node ladder for every cell).
