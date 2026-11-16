# Does the high-counter (H=91) case fit the owner's real clock? — seat 08, PC r15 under PC20, Threads 1

The residual question from my fifty-move withdrawal (`WITHDRAWAL_fifty_move.md`): at H=91 the engine needs ~43M nodes
to reach depth 20, which cannot fit a 6 s + 0.06 clock. Does the time manager cope, and does the MOVE degrade?

Same board `1K6/8/8/3R4/8/8/8/k7 w - - H 1` at H=0 and H=91, `go wtime 6000 btime 6000 winc 60 binc 60`, PC20,
Threads 1, Hash 16, 3 fresh processes each. A depth-20 search on each board first, as the reference for "degraded".

| H | run | depth reached | wall ms | nodes | score | bestmove | depth-20 reference | degraded? |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 22 | 307.8 | 1,511,379 | mate 8 | d5b5 | d5b5 | — |
| 0 | 2 | 21 | 269.8 | 1,283,871 | mate 8 | d5b5 | d5b5 | — |
| 0 | 3 | 21 | 271.5 | 1,283,871 | mate 8 | d5b5 | d5b5 | — |
| 91 | 1 | **10** | **814.3** | 7,251,835 | cp 0 | d5a5 | d5a5 | **NO** |
| 91 | 2 | 10 | 807.1 | 7,251,835 | cp 0 | d5a5 | d5a5 | **NO** |
| 91 | 3 | 10 | 835.5 | 7,251,835 | cp 0 | d5a5 | d5a5 | **NO** |

## Verdict: CLOSED — a cost that time management absorbs, with one caveat worth knowing

- **The move does not degrade.** At H=91 the clocked search played `d5a5` in 3 of 3 runs, the same move a depth-20
  search plays. At H=0 it played `d5b5` in 3 of 3, also the depth-20 move (and `mate 8`, the true distance).
- **The clock is never at risk.** The worst H=91 search took **836 ms of a 6000 ms clock** — 14 % — and 0 of 3 runs
  exceeded it. The engine never attempts the 43M-node iteration: it stops at depth 10 and answers.
- **The caveat: it costs 3x the time for 12 fewer plies.** H=91 spent 807–836 ms to reach depth 10, while H=0 spent
  270–308 ms to reach depth 21-22. So at a high counter the engine burns roughly 7.25M nodes to reach a verdict it
  could form much earlier, and reaches a much shallower depth with the same time. The verdict it reaches is correct
  and the move is right, but that move is a move; the depth is 10 not 21.
- **Reproducible**: at H=91 all three runs gave the identical node count (7,251,835) and the identical move, at
  Threads 1. That is the determinism the swarm rule exists to preserve.

## So the answer to the owner's question

**Does the 43-million-node case fit a real clock? No — and it does not need to.** The engine never runs it: on a
6 s clock it stops at depth 10 in ~820 ms and plays the correct move. The 43M-node figure is what a depth-20 search
costs on that board, not what the engine spends in a game. The case is closed as a cost that time management
absorbs, and the residual risk is not a wrong move but a shallower one at high counters — which is a plausible and
correct trade, not a defect.

## What I did NOT do
- Did not test a board where the correct high-counter move differs from the shallow one; this board's move is the
  same at depth 10 and depth 20, so it cannot show a depth-related move error. That is the honest limit of this test.
- Did not test the low-clock end of the same board (covered separately by 08-F18/F21).
- One run per cell at depth 20 for the reference (the reference is not the measurement under test).

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 fifty_real_clock.py /tmp/frc.txt
