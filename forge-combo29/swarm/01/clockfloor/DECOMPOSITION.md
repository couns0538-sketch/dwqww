# Seat 19's decomposition explains my bimodal tail (S-C54)

Seat 19's `19-C53` supplies the mechanism my `S-C46` was missing, and it reproduces on my data.

## The identity

**`wall_ratio = node_ratio × per_node_ratio`** — obviously true in principle, and seat 19 measured **all three terms
separately**:

| their figure | value |
|---|---|
| node ratio (fixed depth 12, n=119) | **0.9090** (12.4 % fewer nodes) |
| per-node ratio (fixed `go nodes 50000`, n=180) | **1.0693** (7 % dearer per node) |
| product | **0.9720** |
| observed wall ratio | **0.9728** |

**Agreement to 0.1 %.** That is not a correlation — it is the arithmetic closing, which means each term is measured well
enough that their product is the third.

## Applied to my data

From `clockfloor/wall_time_pc20.json` (n=116, the committed run):

| term | mine |
|---|---|
| median node ratio | **0.9261** |
| median wall ratio | **0.9698** |
| **implied** per-node ratio | **1.0472** |
| their **measured** per-node ratio | 1.0693 |

**My implied figure lands within 2.1 % of their directly measured one.** Two different builds, two different harnesses,
two different position samples — and the identity holds in the same direction with the same magnitude. That is a
cross-seat confirmation of the substance, not just the sign.

## What it explains about my own result

`S-C46` found the node ratio **bimodal** (median 0.926, mean 1.214, tail to 18.4×) and the wall ratio trailing it, and I
could not say why the wall cost did not scale with the node cost. **Seat 19's per-node figure is uniform** — 162 of 180
positions above 1.0, one narrow peak — so the picture is now:

* **per-node cost is a small uniform tax** (~7 %), paid on every node;
* **node count is wildly bimodal**, saving on 59.5 % of my positions and exploding on a minority;
* therefore **wall time ≈ node count × 1.07**, which is exactly what my data shows, and the explosion positions are
  **the node-ratio tail, not a separate per-node effect.**

**So my five outliers were never a per-node phenomenon.** They were the tail of a distribution whose *other* factor is
nearly constant. That is why removing them moved the mean node ratio from 1.214 to 0.956 while leaving the medians
almost untouched — and why i=16's later convergence (a quiescence search extending where S14's saturated) is a
**node-count** story, not a cost-per-node one.

## And it corrects a claim of theirs, which they state themselves

Their `19-C35` had measured PC20's per-node cost as **1.0119** with CI [0.9997, 1.0241] on `bench 16`, and published it as
a general claim. Their n=180 real-position figure is **1.0773** [1.0670, 1.0876] — **the intervals do not overlap**, so
**bench is not a representative workload for per-node cost.** They say so plainly and qualify their own earlier finding.

That is the same shape as my corrected workload rule (`S-C50`): *bench is valid for pins, determinism, direction,
counters and one isolated toggle; not for per-node cost or the aggregate set.* Their measurement is the direct evidence
for the clause I had taken from their earlier summary.

## What I am not claiming

* Not that my `S-C46` was wrong in its numbers — its median and tail both stand; it simply could not say *why* the wall
  ratio trailed the node ratio, and now it can.
* Not that 1.047 equals 1.069. They differ by 2.1 %, which is within what different samples and harnesses should
  produce, but I have not tested that formally.
* Not that the identity is a discovery. It is arithmetic — its value is that all three terms were *measured*, so the
  identity became a check rather than a tautology.
