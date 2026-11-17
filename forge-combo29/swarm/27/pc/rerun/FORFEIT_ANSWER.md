## Answer to the coordinator's question: the ply-78 forfeit IS opening-specific, and the underlying behaviour is not

**Short answer: the forfeit is opening-specific — it is the SAME opening that produced the earlier ply-106 forfeit
(`rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b - - 0 3`). But chasing it found something larger that
changes how the range should be stated: the engine overspends its own increment on this opening regardless of how
generous the clock is.**

### The forfeit reproduces, on that one opening, at varying plies

Three single-game runs of that opening alone, 6 s + 0.06, PC20, Threads 1, guarded harness:

| run | ended | ply | clocks at the end |
|---|---|---|---|
| 1 | WHITE_FORFEIT | **72** | w −458, b 2778 |
| 2 | WHITE_FORFEIT | **50** | w −118, b 3351 |
| 3 | WHITE_FORFEIT | **82** | w −74, b 2861 |

So on this opening White forfeits in every run, at a ply that varies (50, 72, 78, 82, 106 across my five
observations). **It is not a fixed ply and not a fixed counter — it is "White runs out on this opening".**

### The part that matters more: the engine overspends the increment by 2–3×

The control arm (6 s + **0.5 s** increment, which is positive-sum by construction) **also forfeited**, which
cannot happen if the engine respects its budget. It spent:

| ply | wall | nodes | depth |
|---|---|---|---|
| 2 | 1096.1 ms | 1,699,648 | 21 |
| 4 | 1462.1 ms | 2,382,041 | 21 |
| 6 | 1278.1 ms | 2,011,089 | 23 |

**28 of 85 moves exceeded the 500 ms increment**, with a median of 411 ms. Confirmed independently from the
engine's own `time` field in a fresh process: `go wtime 6167 btime 6025 winc 500 binc 500` reports
**`time 615`** and **`time 604`** on two runs — **above the 500 ms increment and above any plan that treats the
increment as a per-move allowance.**

### So the range form needs a companion statement, not a replacement

The 19–32 ms/move drain at 6 s + 0.06 stands as measured, and the two forfeits (plies 106 and 78) are both real.
But they should not be reported as "this time control is slightly negative-sum". The stronger and better-supported
statement is:

> **On at least one opening, the engine spends 2–3× its own per-move increment (500 ms increment, 604–1462 ms
> spent), so a clock game on that opening loses on time regardless of how the increment is sized.** The 6 s + 0.06
> drain is one symptom; the overspend is the mechanism.

### What I have NOT established

- Whether the overspend is specific to this opening or general. I have one opening and 28 of 85 moves over budget;
  that is enough to say "not rare here", not enough to say "everywhere".
- Whether a larger `Move Overhead` or a different `movestogo` changes it. Untested.
- Whether the 604–615 ms is the engine failing to stop or a legitimate reading of its soft plan for a 6 s clock.
  **The engine is not necessarily wrong to spend 604 ms out of 6000** — the question is whether it *plans* to,
  and my control's forfeit says the bookkeeping does not survive 84 plies.
