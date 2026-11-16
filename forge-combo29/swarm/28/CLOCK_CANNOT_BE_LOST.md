# The clock cannot be lost to a search — the structural result

> ## THE MARGIN: MoveOverhead + increment = **70 ms at the owner's control**, at EVERY clock size.
>
> That single number is the whole safety argument. A move can only lose the game on time if its total wall
> time exceeds `clock + increment`; the search is capped at `clock − MoveOverhead`, so the shortfall is
> always at least `MoveOverhead + increment` — 10 + 60 — no matter whether the side has 6 seconds or 30 ms
> left. Nothing about the engine's speed, the position, or the depth reached changes that.

A clean result to hold onto, stated exactly.

## The inequality

From `include/forge/clock_plan.hpp`, with `available = clock − MoveOverhead`:

```
moves_to_go = 0 :  hard = min(available * 60/100, soft * 5)
moves_to_go > 0 :  hard = min(available * 80/100, soft * 4)
either branch   :  hard = max(1, min(hard, available))      <- the final clamp
```

so in every case

```
        hard <= available = clock - MoveOverhead
```

A search spends at most `hard`, and a side loses on time only when its spend exceeds
`clock + increment`. Therefore

```
        spend <= hard <= clock - MoveOverhead < clock + increment
```

for every `MoveOverhead >= 0` and every `increment >= 0`. **The margin is `MoveOverhead + increment` —
70 ms at the owner's control — and it is constant at every clock size.**

This does not depend on the 60 % or 80 % constants, nor on `soft`, nor on the divisor, nor on `movestogo`:
the final clamp alone guarantees it. The percentages only make the spend smaller than the bound.

## What it means

**Spend is proportional to what remains, so the clock cannot run out from searching.** A side at 500 ms
plans at most 294 ms; a side at 111 ms plans at most 60 ms; a side at 30 ms plans at most 12 ms. The engine
gets slower in proportion to how little time it has, which is the correct behaviour and not a lucky outcome.

Measured, 1,090 moves in 10 real games at 6 s + 0.06 (S-F39, S-F40): **0 flags**, and the constructed
adversarial case (4 complex middlegames at clock 300/200/150/111 ms, S-F41) also produced **0 flags**, with
actual spends of 22–50 ms far below even the plan.

## The fixed point: the clock converges to a floor, from any starting clock

The strongest safety statement available, because it is exact rather than measured.

**The derivation.** The clock rule is `clock' = clock − spend + increment`. A fixed point needs
`spend = increment`. The most a search can spend is its hard plan
`hard = min((clock − MoveOverhead) · TmHardPercent/100, soft · TmHardSoftMultiple)`, so take the
worst case (every search spends its full cap). At these constants the percent term binds — the other
term would require a negative available — so the fixed point satisfies

```
        (clock − MoveOverhead) · TmHardPercent / 100 = increment
    =>  clock = MoveOverhead + increment · 100 / TmHardPercent
    =>  clock = 10 + 60 · 100 / 60 = 110 ms
```

**Iterating the real rule converges to that value from every starting clock** (worst-case spend):

| starting clock | clock after 100 moves | hard plan at the fixed point |
|---|---|---|
| 6000 | **111** | 60 |
| 3000 | **111** | 60 |
| 1000 | **111** | 60 |
| 500 | **111** | 60 |
| 300 | **111** | 60 |
| 200 | **111** | 60 |
| 150 | **111** | 60 |

The 1 ms difference from the closed form is integer division in the plan. So the clock approaches ~111 ms
and **stops falling**: at that point the search spends exactly the increment each move. A game of 165, 400
or 10,000 plies cannot forfeit by searching.

**Two precisions that matter:**
1. **111 ms is the floor under the WORST case** — every search spending its full hard cap. Typical spend is
   nearer the soft plan, which at a 6 s clock is `590/22 + 45 ≈ 72 ms` against a 60 ms increment, so the
   clock declines only ~12 ms per move and settles far higher. The measured games settled at 111–120 ms and
   174–300 ms, both consistent. The worst case is the bound; reality is gentler.
2. **The hard cap is a bound, not a target.** Measured directly: with `TmHardPercent` set to 30/45/60 at
   clock 600 on a long-iteration position, the caps are 177/266/354 ms but the measured spends are 86/86/34
   ms — the engine stops at its soft plan well inside the cap. So the floor holds because spend cannot
   exceed the cap, not because the engine deliberately spends it.

### The constants caveat, stated exactly
The floor is **`MoveOverhead + increment · 100 / TmHardPercent`**. So it moves with those three quantities:

| TmHardPercent | floor at overhead 10, increment 60 |
|---|---|
| 30 | 210 ms |
| 45 | 143 ms |
| 60 | 110 ms |
| 75 | 90 ms |
| 90 | 77 ms |

**It does NOT depend on `TmSoftDivisor` or `TmIncrementPercent` at these constants** — I checked, and the
`soft · TmHardSoftMultiple` term cannot bind here, so the divisor and the increment percentage are not part
of the floor. Raising `TmHardPercent` (a more generous cap) LOWERS the floor, which is the direction that
matters: a looser cap means the engine can be driven closer to zero. The floor is bounded below by
`MoveOverhead + increment` in the limit `TmHardPercent → 100`.

## The clock row is stable under CPU contention in everything but wall time

Seat 05's S-F49 recorded that its clock row varied under load and offered that as a caveat. I tested it
directly on my own harness (PC r15 + PC20, Threads 1, Hash 16): the same position at `go wtime 6000 btime
6000 winc 60 binc 60`, three times alone and three times with a busy loop saturating every other core.

| condition | depth | nodes | wall ms | bestmove |
|---|---|---|---|---|
| solo run 1 | 18 | 998994 | 589 | d1b1 |
| solo run 2 | 18 | 998994 | 647 | d1b1 |
| solo run 3 | 18 | 998994 | 591 | d1b1 |
| under load 1 | 18 | 998994 | 593 | d1b1 |
| under load 2 | 18 | 998994 | 598 | d1b1 |
| under load 3 | 18 | 998994 | 601 | d1b1 |

**Depth, node count and move are identical in all six runs**; only wall time moves, 589-647 ms, a 10 %
spread. The searched result is bit-identical whether the machine is idle or loaded.

**Why, and why it matters here:** a clock search stops at the end of a completed iteration, so its node
count is a STEP FUNCTION of the time available. A 10 % shift in wall time does not cross an iteration
boundary and therefore changes nothing; only contention severe enough to cost a whole iteration can move it,
and then it moves in a discrete jump (seat 05 saw 784,328 -> 542,082, a 45 % drop, which is exactly such a
jump). So the clock control is not fragile: it is quantised, and it takes a lot of load to move one quantum.

That also means a contention-stressed run is not a wrong measurement — it is a measurement of a LOWER rung of
the same ladder. The depth number alone should be read as "the rung reached", not as a continuous quantity.

## The residual risk — the three ways a side could still flag

A flag needs one move's **total** wall time to exceed `clock + increment`. Since the search cannot do that,
only these three can:

1. **A plan violation** — the engine spending more than its own computed `hard`. This would be a bug in the
   time manager or the stop path. It did not happen in 1,090 measured moves, but it is the one failure the
   arithmetic above cannot exclude, because the arithmetic assumes the engine obeys its own plan.
2. **A stall outside the search** — process scheduling, GUI latency, an OS pause, or the engine being slow
   to print `bestmove` after the search ends. The clock a GUI deducts covers the whole move, not just the
   search loop, so a stall is invisible to the plan and can exceed the margin. Nothing in my runs shows it,
   and my harness measures wall from `go` to `bestmove`, so a large stall would have appeared as a large
   wall time — the max observed was 792 ms against a plan that allowed more.
3. **A refused position** — an invalid FEN or an illegal move in `position ... moves` leaves the PREVIOUS
   position on the board (S-C4/21-F2), so the engine may search a board the GUI did not intend, and after a
   `stop` or a refused position the move timing can differ from what the plan assumed.

Of the three, only (2) is a real risk at the owner's control and it is a property of his machine and GUI,
not of the engine. (1) is a code-correctness question already covered by the sanitizer and honesty work.
(3) needs a malformed input, which a match program does not send.
