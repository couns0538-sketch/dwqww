# RISK OF THE S-F19 REPAIR, MEASURED (not argued)

Seat 25. Variant: same PC r15 source with the fifty-move branch in `Worker::is_draw` compiled out
(`FORGE_CLOCK99_NORULE50`). Patch: `FORGE_EXPERIMENT_remove_rule50_from_is_draw.patch.txt`. Build
`/home/ubuntu/build/var50/forge`. Threads 1, Hash 16, PC20, depth 10.

**Honesty check first:** the variant reproduces all four pins exactly (312866 / 862329 / 3024920 / 4865609), so it
is a controlled single-change comparison and its numbers are usable.

## The measurement

Ten purpose-built positions (pawnless, capture-free, so the fifty-move region is genuinely reachable), each at
clocks 95, 97 and 99 -> 30 cells. A = fifty-move test present, B = test removed.

| group | cells | mean gap (B-A) | mean \|gap\| | max \|gap\| |
|---|---|---|---|---|
| G1: A says 0 AND position is dead drawn | 6 | -80.2 | 146.2 | 235 |
| G2: A says 0 but a real result exists | 24 | -237.1 | 367.4 | 1230 |
| G3: A was not fooled | 0 | - | - | - |

**Node cost: median ratio 407.9x, maximum 1,025,974x.**

## What this means, honestly

I predicted the risk as "quiet lines slightly overvalued, a few centipawns". **I was wrong about the size, and the
node cost is the part that decides it.**

1. **The score gap is not a few centipawns.** Mean absolute difference 323 cp across all 30 cells, 367 cp in the
   group that matters, maximum 1230 cp. In G1 the variant calls dead-drawn endings (K+N v K+N, K+R v K) worth up to
   -235/-416/-1230 cp: that IS the overvaluation I predicted, and it is large, not small.
2. **The node cost is disqualifying on its own.** Median **408x** more nodes, and on the worst cell 1,025,974x
   (50 nodes -> 51,298,729 nodes). Removing the test means the engine searches the entire fifty-move region of
   every quiet line instead of stopping at it. At a fixed movetime that is not "slightly shallower results", it is
   a collapse in usable depth in exactly the endings where deep search matters most.
3. **G2 is not evidence FOR the fix.** In several G2 rows the variant's number is the better one (e.g.
   `6K1/8/8/k1q5/...`: A says 0, B says -1215, and white really is lost against a queen), which shows the current
   code is buggy there. But you cannot buy that correction at 400x the nodes.

## So the recommendation changes

**Do not remove the fifty-move test from `is_draw`.** My S-F19 proposal said remove it; the measurement says the
cure is far worse than the disease. I am withdrawing that recommendation and recording why, since an unmeasured
proposal was what I offered and this is the number that refutes it.

**The narrower repair I would now choose** (still a proposal, still untested, patch stays EXPERIMENT): keep the
short-circuit, but make the test *refusable-aware* instead of removing it:

    a node at clock >= 100 is a draw ONLY IF no capture or pawn move is available to either side
    in the position (i.e. nobody can reset the counter);
    otherwise search it.

That targets exactly the demonstrated bug (a reset was available, so the draw was claimable and refusable) and it
leaves the 400x node cost to the case that genuinely needs it: the forced draw, where the engine should stop anyway.
Whether it costs nodes in practice is the next thing to measure, and I have not measured it.

## What I did NOT do
- I did not implement or measure the narrower repair above.
- Ten positions is a small sample; the 408x median is striking enough that I would not expect a different verdict
  from more, but I am not claiming a population figure.
- I did not test the variant at other depths or with a clock, only fixed depth 10.
