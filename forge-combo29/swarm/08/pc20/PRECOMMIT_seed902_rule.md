# Pre-committed reporting rule for the seed-902 sparse replication — seat 08

Written and pushed BEFORE the seed-902 run finishes, so the reporting decision cannot be shaped by the result.
(This is the same discipline as committing a prediction before measuring.)

## The question
08-F31 measured, on the sparse class (≤12 pieces, from R seed 801), **10 of 27 boards (37 %) where the clocked score
was a centipawn evaluation and a completed `go depth D+4` found a mate**. That is the single number from the
training-data work the owner might act on. If it is an artefact of that one 500-position sample, it is not a rate.

## The rule I will apply, fixed now

Let the seed-902 sparse sample give **k successes in n usable boards**, with a 95 % Wilson interval.

1. **If the seed-902 rate falls inside 37 % ± 15 points (i.e. 22 %–52 %)**, I report the finding as a RATE and quote
   BOTH samples' counts side by side. I will not average them into one figure — I will say "10 of 27 and k of n",
   because two samples of this size do not justify a pooled point estimate.
2. **If it falls outside 22 %–52 %**, I say plainly: **"the rate is NOT ESTABLISHED"**, quote both counts, and
   demote the finding from a rate to a direction — i.e. "the sparse class contains boards where the clocked score
   misses a mate", with no percentage attached. I will not average the two samples to hide the disagreement.
3. **If fewer than 15 usable boards complete** in a reasonable time, I report the count I got as an observation and
   state that the replication is INCOMPLETE — not that it agrees or disagrees.

## Why ±15 points
With n ≈ 27 and a true rate near 37 %, the 95 % interval on a single sample is roughly ±18 points. Two samples whose
point estimates are within 15 points are not distinguishable at this size; two further apart are evidence of
heterogeneity between samples, which would itself be worth reporting (and would mean the rate depends on how the
sparse positions are generated).

## What I will NOT do
- Average the two rates into a single number.
- Report the better-looking one.
- Describe a disagreement as "consistent within sampling noise" without showing the interval.
- Change this rule after seeing the number.
