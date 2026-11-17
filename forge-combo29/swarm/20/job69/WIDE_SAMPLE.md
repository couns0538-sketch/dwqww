# seat 20 — job 69: the own-8MB variant on 20 positions — median 0 cp, p90 18 cp, max 73 cp

S-F58 passed on 5 positions. The stated next step was a wider sample at a stated tolerance. Done: **20 G-set
positions, 60 alternate-line comparisons**, candidate (own 8 MB table at Hash 2048) against the **healthy** reference
(same build, Hash 16), MultiPV 3, `go wtime 5000`, Threads 1, machine certified clean.

## Pre-stated tolerance (written before measuring)
*Pass if the 90th percentile of |difference| across all positions × alternate lines is ≤ 100 cp **and** no single line
moves more than 500 cp.* Those are my judgement calls and are labelled as such — an owner can substitute his own and
re-read the same distribution.

## Result

| statistic | value |
|---|---|
| comparisons | **60** (20 positions × 3 lines) |
| median \|difference\| | **0 cp** |
| 90th percentile | **18 cp** |
| maximum | **73 cp** |
| within 10 cp | **52 of 60** |
| main-line depth | reference median **14**, candidate median **14** |

**PASS**, comfortably: the worst single line in 60 moved 73 cp, against 775–988 cp for the two rejected variants, and
the main line does not lose depth.

## The question to put to the owner — stated as a question, not a recommendation
**"Is a candidate that reproduces the healthy build's alternate lines to within 0 cp median / 18 cp p90 / 73 cp max
acceptable, or do you require bit-identical alternate scores?"**

- If he accepts this tolerance, the direction is viable and worth hardening (MultiPV 2/8, longer clocks, saturation).
- If he requires bit-identical, **this candidate does not meet it** — 8 of 60 lines moved at all — and the requirement
  becomes much harder, because the alternate table is smaller by design and a smaller table will occasionally resolve a
  bound differently.

Either answer is a decision he can make from this table; it is not mine to make for him.

## Limits
- G-set positions only (game positions the swarm already uses); no endgames, no long games where an 8 MB alt table
  might **saturate** — untested, and the most likely place this breaks.
- MultiPV 3 only; one clock (5 s); built-in net; Threads 1.
- "Healthy reference" is itself a search, not ground truth — I am measuring *reproduction of normal behaviour*, not
  correctness against an oracle.
