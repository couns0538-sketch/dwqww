# The clock cannot be lost to a search — the structural result

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
