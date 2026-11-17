## S-W4: my clock harness's wall time includes ~1300 ms of MY OWN overhead — the "overspend" figures are withdrawn

This corrects S-C11d and S-C11e, and it is the same class of error as S-W1: a plausible number produced by the
measurement apparatus rather than by the engine.

### The measurement that exposed it

A depth-1 search — which the engine reports as **`time 0`** — takes **1300 ms** of wall time through my harness:

| run | wall through my harness | engine's own `time` |
|---|---|---|
| 1 | 1304 ms | **0 ms** |
| 2 | 1299 ms | **0 ms** |
| 3 | 1300 ms | **0 ms** |

**1300 ms per call is Python interpreter startup plus `subprocess` spawn plus the `uci`/`setoption`/`isready`
preamble**, all of which I was charging to the search. My `check_15f35_clock.py` measures

```python
t0 = time.monotonic()
self.s(cmd)                      # the go line
lines, ok = self.until(...)      # read to bestmove
wall = (time.monotonic() - t0) * 1000.0
```

which *should* exclude startup — but the clock bookkeeping then subtracts that wall from the game clock, and any
row where the process had to be re-spawned (the WARM policy reuses one process per game, but a fresh process is
started in some paths) carries the full 1300 ms. **The 4280 ms maximum and the 2910 ms maximum are consistent with
~1300 ms of harness overhead plus a genuine search, not with a search that overran by 3848 ms.**

### The direct check, which is what settles it

Fresh process, `go wtime 732 btime 3000 winc 500 binc 500` — the clock state at the ply-84 row — three runs:

| run | engine's own `time` | planned hard limit | verdict |
|---|---|---|---|
| 1 | **329 ms** | 433 ms | within the plan |
| 2 | **328 ms** | 433 ms | within the plan |
| 3 | **322 ms** | 433 ms | within the plan |

**The engine reported 322–329 ms against a hard limit of 433 ms. It did not overrun.** So the "6 of 85 moves
exceeded the hard limit" table was measuring my harness, not the engine.

### What this withdraws and what survives

**Withdrawn:**
- S-C11d's "engine spends 2–3× its per-move increment" — the 1096/1462/1278 ms figures were harness wall.
- S-C11d's "the control arm forfeited because of overspend" — the control's forfeit is explained by the harness
  charging ~1300 ms per move to the clock, which drains any clock regardless of the engine's behaviour.
- S-C11e's "32.9 % / 32.0 % of moves exceed the 500 ms increment" — same cause.
- **S-C11c's guarded re-run drain of 31.9 ms/move and the ply-78 forfeit** — same cause.

**Survives, and now needs re-measuring with the engine's own `time` field instead of wall:**
- That a clock game on `rnbqk1nr/pppp1ppp/3b4/...` ran out of time (the forfeit was real in the sense that the
  clock bookkeeping went negative, but the bookkeeping used harness wall).
- The plan arithmetic itself: at 6 s + 60 ms the soft/hard plan is 317/1585 ms; at 6 s + 500 ms it is 647/3235 ms.
  These are computed from `clock_plan.hpp` and are unaffected.

### The fix, and it is the same lesson as S-W1

**Never use caller-measured wall as the engine's think time.** The engine publishes its own `time` field on every
`info depth` line — use that, and use wall only for the total including your own apparatus, labelled as such.
My earlier tables are exactly the error this rule prevents.

**Third instance of the same class in one session:** S-W1 (zero info lines), S-W3 (undefined exception), S-W4
(harness overhead in the clock). All three produced or nearly produced a published number that described the
measuring apparatus rather than the engine.
