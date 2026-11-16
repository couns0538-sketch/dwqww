# `go softnodes N` — determinism, finished depth, overshoot — seat 08

PC r15, PC20, Threads 1, Hash 16, 5 fresh processes per cell, 2 positions x N ∈ {500, 2000, 20000}.
Independent harness (`softnodes.py`), written from FABLE_TO_swarm_6's description only.

## The three answers

| position | N | deterministic? | bestmove | last depth | nodes at stop | overshoot past N | finished depth? |
|---|---|---|---|---|---|---|---|
| startpos | 500 | **YES** | d2d4 | 5 | 971 | **+471** | YES (pv present) |
| startpos | 2000 | **YES** | d2d4 | 7 | 4,121 | **+2,121** | YES (pv present) |
| startpos | 20000 | **YES** | d2d4 | 12 | 21,600 | **+1,600** | YES (pv present) |
| G middlegame | 500 | **YES** | g7g6 | 4 | 626 | +126 | YES (pv present) |
| G middlegame | 2000 | **YES** | g7g6 | 7 | 2,671 | +671 | YES (pv present) |
| G middlegame | 20000 | **YES** | g7g6 | 12 | 31,779 | **+11,779** | YES (pv present) |

| quantity | value |
|---|---|
| cells measured | 6 |
| cells NOT deterministic | **0** |
| largest overshoot past N | **11,779 nodes** (N=20000 on the middlegame) |

1. **Deterministic: yes, 6 of 6 cells**, identical bestmove, identical node count and identical last depth in
   every one of 5 fresh processes. Nothing varied at Threads 1 — including the 7,251,835-node case elsewhere.
2. **Stops at a finished depth: yes**, every cell's final `info depth` line carries a `pv`, so the stop lands at a
   completed iteration rather than mid-iteration.
3. **How far past N: up to 11,779 nodes (59 %) at N=20000, and up to 2,121 (424 %) at N=2000.** The overshoot is
   one iteration: the cap is checked when an iteration finishes, so a cheap N can be exceeded by a whole iteration's
   cost. At the owner's `softnodes 2000` the measured spend was **2,671–4,121 nodes, i.e. 1.3x–2.1x the budget.**

## The one thing worth flagging for the owner's self-play
`go softnodes 2000` does not mean "spend 2,000 nodes": measured, it spends **2,671 nodes on the middlegame and 4,121
on startpos at depth 7**. If the self-play's cost model or its reproducibility depends on the node figure, the
number to use is 1.3x–2.1x N, not N. That said, the behaviour is perfectly deterministic, which is what the
self-play actually needs.

## Show it again
    cd forge-combo29/swarm/08/softnodes && python3 softnodes.py /tmp/sn.txt
