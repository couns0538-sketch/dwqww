# Six slices: the per-node factor is the stable one (S-C65, corrected)

**Correction in place.** An earlier block said *"only the per-node factor moves with phase."* **That was backwards**, and
thirds were too coarse to show it. Six slices of the population (4,135 pairs, ~689 each):

| slice | node median | per-node median | wall median |
|---|---|---|---|
| 1 | 0.9595 | 1.0696 | 1.0083 |
| 2 | 0.9618 | 1.0714 | 1.0476 |
| 3 | 0.9618 | 1.0707 | 1.0364 |
| 4 | 0.9535 | 1.0691 | 1.0213 |
| 5 | 0.9626 | 1.0713 | 1.0476 |
| 6 | 0.9613 | 1.0715 | 1.0189 |
| **spread** | **1.36 %** | **0.29 %** | **4.76 %** |

**Per-node cost is nearly a constant of the engine — 0.29 % across every slice — and the phase-dependence lives in the
node ratio.** So `wall = node × per-node` varies almost entirely through `node`.

## The caution: the identity does NOT close row by row

**A median of a product is not the product of medians**, so a reader must not multiply each row and expect the wall
median. Checked:

| slice | node × per-node | wall median | difference |
|---|---|---|---|
| 1 | 1.0263 | 1.0083 | **+0.0180** |
| 2 | 1.0304 | 1.0476 | **−0.0172** |
| 3 | 1.0298 | 1.0364 | −0.0066 |
| 4 | 1.0194 | 1.0213 | −0.0019 |
| 5 | 1.0312 | 1.0476 | −0.0164 |
| 6 | 1.0301 | 1.0189 | **+0.0112** |

**Per-slice differences run ±0.018 in both directions.** On the **aggregate** the identity closes to **0.0004**
(0.9618 × 1.0707 = 1.0298 against a wall median of 1.0294).

**So the identity is a statement about the population, not about any row of the table above.** A reader who tests it
row-by-row will find apparent failures that are not failures, and might conclude the decomposition is wrong when it is
the multiplication that is wrong.

## Why the corrected mechanism matters more than the original

**Per-node cost is a property of the CODE**, and it is stable to 0.29 % across every game phase.
**The node ratio is a property of the SEARCH interacting with the position**, and it is what changes between opening and
endgame.

That is why three independently obtained per-node figures agree:

| source | per-node |
|---|---|
| seat 19, implied at n=464 | **1.0640** |
| seat 19, direct fixed-node at n=180 | **1.0693** |
| seat 01, population n=4,135 | **1.0707** |

**Three samples, two builds, three sample sizes — because it is the one term that does not depend on what you sampled.**

## The resolution lesson, as a rule

> **Before splitting a population by phase, ask how large the smaller variation is relative to the number of slices.**

My thirds found nothing because the factor I was looking for varied by **0.29 %** while the factor I was looking at
varied by **1.36 %** — a factor four times smaller needs far more slices than three to separate from noise. **The failure
mode is not "no answer"; it is a confident answer pointing the wrong way**, which is what the thirds gave me: I read a
stable per-node factor as the moving one.
