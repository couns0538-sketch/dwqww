## Second opening: the overspend is GENERAL, the forfeit is what is opening-specific

Correction to my own S-C11d framing. I said "on this opening the engine spends 2–3× its increment", implying the
overspend might be specific to that opening. **A second opening shows the overspend is general and only the
forfeit is opening-dependent.**

Both arms at 6 s + **0.5 s** increment (positive-sum by construction), PC r15, PC20, Threads 1, Hash 16,
OwnBook false, guarded harness:

| opening | plies played | median wall | moves > 500 ms | share | max | ended |
|---|---|---|---|---|---|---|
| 1 `rnbqk1nr/pppp1ppp/3b4/...` (the forfeiting one) | 85 | 411 ms | **28 of 85** | **32.9 %** | 4280 ms | WHITE_FORFEIT |
| 2 `rnb1kbnr/ppp1pppp/8/4q3/...` | 200 | 375 ms | **64 of 200** | **32.0 %** | 2910 ms | PLY_CAP (survived, 4255/1869 ms left) |

**The overspend rate is the same to within a point — 32.9 % versus 32.0 %.** So the engine overspends its
500 ms increment on roughly a third of moves **in both openings**, and that is a general behaviour, not a
property of the forfeiting one.

**What is opening-specific is whether that costs the game.** Opening 1 ran out at ply 84 with both sides spending
similarly; opening 2 finished 200 plies with 4255 ms left for White. The difference is which side's search is
expensive relative to its own clock, not that one opening triggers overspending and the other does not.

### The corrected statement for the owner

> **The engine spends more than its per-move increment on about one move in three, in both openings tested
> (32.9 % and 32.0 % of moves exceed a 500 ms increment).** That is general behaviour, not an opening quirk. Whether
> it loses the game depends on the position: on opening 1 it forfeited by ply 84; on opening 2 the same policy
> finished 200 plies with 4.3 s and 1.9 s still on the clocks.

And at the owner's real control (6 s + 0.06), the drain is a **range of 19–32 ms per move** across my runs
(zero-crossing 188–322 plies), with **opening 2 giving 27.2 ms/move and 220 plies** — inside that range.

### The three open questions, now sharper

1. **Is 604 ms on a 6000 ms clock a violated hard limit or a legitimate plan?** Still open, and now the important
   one. A plan that gives 604 ms out of 6000 is defensible; spending 2910–4280 ms on a single move in a 6 s game
   is much harder to defend, and I have those maxima recorded but have not yet separated "the plan said so" from
   "the plan was abandoned". **This is the measurement to run next**: compare the engine's own `time` field
   against the soft plan the engine computed for that move.
2. **How many openings overspend?** Two of two so far, at ~32 % of moves. That is enough to call it general; more
   openings would only refine the rate.
3. **Do `Move Overhead` or `movestogo` change it?** Untested.

### What this corrects in my own record

S-C11d said "on this opening the engine spends 2–3× its increment, so a clock game loses on time regardless of
increment size". The first half is right and is **general**; the second half is only true **for positions where
the overspend lands on the side with less clock**, which is what happened on opening 1 and not on opening 2.
