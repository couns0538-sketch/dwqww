# Can the engine know, at abandon time, that the in-flight iteration will be discarded?

Answer to the design question flagged in S-F37. **Read from the source, not built.**

## Short answer: mostly yes, and the one exception is narrow but real

- A **completed** iteration publishes its result at a single point, after the search call returns
  (`src/search.cpp:2454-2461`: `result.score`, `result.depth`, `result.pv`, `result.best_move`,
  `result.ponder_move`, `result.nodes`). Nothing observable escapes during an iteration.
- **But the abort path deliberately publishes a partial line.** `src/search.cpp:2439-2451`, when
  `aborted_` is set and `!stopped_by_nodes_`, the engine assigns `result.best_move = ss->pv[0]` from the
  *unfinished* iteration and calls `emit(depth, result.score, result.pv)`, explicitly commented
  "A clock or external stop may keep a root move that already raised alpha in this unfinished iteration".

So the mechanism to abandon mid-iteration **already exists** — `aborted_` + this block is exactly it — and
the question is not "can it be done" but "does abandoning earlier change the move".

## What state an abandoned iteration leaves

From the source, an in-flight iteration that is abandoned leaves:
| state | publication |
|---|---|
| `result.score` | **unchanged** — stays the last finished iteration's score (comment says so explicitly) |
| `result.depth` | **unchanged** — the abandoned depth is not stamped |
| `result.best_move` / `result.pv` | **may change**, only if `ss->pv[0]` exists AND differs from the current best — i.e. a root move raised alpha in the unfinished iteration |
| `result.nodes` | not updated on the abort path (only on the completion path at 2461) |
| transposition table | written continuously by the search; an abandon leaves whatever was stored |
| `emit()` info line | **published** with the revised PV when the move changed |

## Measured: does the move actually change?

On the PC20 worst case (`8/8/6k1/Q7/1P4PP/1K3P2/8/8 b`, 936 ms discarded) and the base worst case
(`8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w`, four consecutive runs):

```
rep0: wall 1586 ms | last info d19 time 1015 pv0 g5h5 | bestmove g5h5 | SAME True | wasted 571 ms
rep1: wall 1586 ms | last info d19 time 1014 pv0 g5h5 | bestmove g5h5 | SAME True | wasted 572 ms
rep2: wall 1585 ms | last info d19 time 1009 pv0 g5h5 | bestmove g5h5 | SAME True | wasted 576 ms
rep3: wall 1585 ms | last info d19 time 1031 pv0 g5h5 | bestmove g5h5 | SAME True | wasted 554 ms
```

**The published move is identical to the last completed iteration's move in all four runs**, and ~570 ms is
spent producing nothing new. So on this board the abort-path publication never fires with a different move —
consistent with the position being lost (score ≈ −1827), where no root move improves on the current best.

## What a fixer should do — and the one risk

**Case B is implementable with a flag, and the mechanism already exists.** The engine already tracks
`aborted_`, already has a "stop now" path, and already knows `hard_limit_ms_`. A targeted version is:

> when the hard limit has passed and no depth has been completed since the soft plan was crossed, stop
> immediately — the iteration in flight cannot be kept anyway.

**The risk, stated plainly:** that condition is *not* the same as "the iteration will be discarded". The
abort path at 2439-2451 will still publish `ss->pv[0]` if a root move raised alpha, and in that case the
abandoned iteration is NOT free — it changes the move, on the strength of a partially searched ply. So:
- if the aim is to skip a search that has completed nothing since soft, the engine can know it has completed
  nothing (a depth counter), and the abandon is safe and free;
- if the aim is to skip a search that might still raise alpha, the abandon can change the move and is
  **not** free — it trades the current best for a partially-searched alternative.

**Recommendation:** gate the abandon on "no depth completed since soft was crossed" (a counter comparison,
not a prediction). That is exactly the S-F31 case, it is knowable at the moment of the check, and it cannot
change the move because no new depth was published.

## What this does not settle
- I did not build or patch anything; this is a reading of `src/search.cpp` plus a measurement of one board.
- Whether the same holds across many sparse endgames is untested. The four runs are one position repeated.
- The abandon also leaves whatever the iteration wrote into the transposition table. That is normal for any
  abort and presumably harmless, but I did not verify it does not change a later move in a game.
