# What a mid-iteration abandon would buy — and why the free half is the interesting one

Arithmetic on committed data, nothing built. The question: the gated rule fires only at iteration
boundaries, so it cannot prevent the cost of the iteration that overran. Would abandoning INSIDE an
iteration be worth the larger change?

**Answer: it depends entirely on which iteration you abandon, and the two cases have opposite economics.
The free one is the whole recommendation; the ply-costing one is not worth it.**

## CASE B — abandoning an iteration that would be DISCARDED anyway: FREE, and it is where the waste is

When the search runs past its last completed iteration to the hard limit, it finishes nothing (S-F31). Time
spent there is pure loss: abandoning costs **zero plies**, because that depth was never going to be kept.

Measured at the owner's real 6+0.06 control (`out_real/realclock_*.tsv`; the span is
`wall_ms − engine_time_ms`):

| build | searches | median discarded span | max discarded span | searches wasting >50 ms |
|---|---|---|---|---|
| base | 60 | 1 ms | 578 ms | 1 |
| PC20 | 60 | 1 ms | **936 ms** | 1 |

The distribution is the point: **59 of 60 searches discard under 5 ms**, and the waste is concentrated in
exactly one search per build:

| build | position | wall | last completed iteration | discarded | depth reached |
|---|---|---|---|---|---|
| base | `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w` | 1585 ms | 1007 ms | **578 ms** | 19 |
| PC20 | `8/8/6k1/Q7/1P4PP/1K3P2/8/8 b` | 1585 ms | 649 ms | **936 ms** | 16 |

So a mid-iteration abandon targeted at the *discarded* case would recover **578-936 ms at zero ply cost**
on 1 search in 60, and do nothing anywhere else. That is a real, safe win on the worst move of the game —
and it is the same class of position (sparse endgames) that the whole thread has been about.

## CASE A — abandoning an iteration that WOULD have completed: costs 1 ply every time

Here the plan is crossed inside an iteration that then finishes. Abandoning at the soft plan saves
`finish − plan` exactly, but throws away the depth being built.

At the true 10 s plan (B = 454), 14 iterations cross soft inside themselves and complete:

| saving | value |
|---|---|
| median | 166 ms |
| mean | 226 ms |
| max | **833 ms** (base #21: started at 48 ms, finished at 1287 ms, depth 30) |
| total | 3,161 ms across the 14 cases |
| ply cost | **1 ply in every single case** |

At the 6 s plan (B = 317, applied to the same 10 s iteration costs — an approximation, labelled as one),
24 iterations qualify: median 52 ms, mean 159 ms, max 970 ms, again 1 ply each.

**This is not a good trade.** A median 52-166 ms for a guaranteed ply is worse than the gated rule's own
terms (which gets its saving with no ply cost on two thirds of positions). The 833-970 ms outliers are
attractive in isolation, but you cannot buy them without also paying a ply on the other 13-23.

## The comparison, which is the whole answer

| change | ply cost | median gain per case | max gain | cases affected | verdict |
|---|---|---|---|---|---|
| gated rule (boundary, S-F34) | 0 or 1 | 35 ms mean | 424 ms | a handful | worth building |
| abandon a DISCARDED iteration | **0** | 1 ms | **936 ms** | **1 in 60** | worth building — free |
| abandon a COMPLETING iteration | 1 ply always | 52-166 ms | 833-970 ms | 14-24 of 48 | not worth it |

## What the owner should take from this
1. **The bigger change is worth considering, but not in the form first imagined.** Abandoning completing
   iterations costs a ply every time and is worse than the gate. Abandoning *discarded* iterations is free
   and recovers up to ~0.9 s on the single worst move.
2. **It is a narrow fix, not a general one:** 1 search in 60. That is exactly the S-F31 pathological case,
   and it is cheap to target because the engine already knows it has an iteration in flight that cannot be
   kept.
3. **The largest cost in the dataset is now covered from two directions:** the gate cannot prevent it
   (S-F36), and a completing-iteration abandon would cost a ply — but the *discarded* abandon recovers the
   tail of it for free.

## Honest limits
- Case A at B = 317 reuses 10 s iteration costs, so its ms are indicative, not measured at 6 s. Case B is
  measured at the real 6+0.06 control.
- Case B's span assumes an implementation can distinguish "iteration in flight that will be discarded" from
  "iteration that will complete" at the moment it abandons. The engine's `should_stop` already knows the
  hard limit; whether it can know the iteration will be discarded before it finishes is the design question
  I have not settled.
- Neither case is a strength claim. A saved millisecond is worth nothing if the move gets worse; a match
  prices that.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 mid_abandon.py
```
Raw: `mid_abandon_out.txt`.
