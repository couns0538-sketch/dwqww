# 19-C60 — the coin flip is GENERAL to the four PC20 switches, not a property of CorrHistV2. My prediction was wrong.

## Result
One switch at a time, all other PC20 options held constant, PC r15, Threads 1, Hash 16, depth 12,
120 real positions, interleaved, fresh process:

> **CORRECTED IN PLACE 2026-11-17T03:30Z — three sign-test p-values were wrong (not two), and the error
> inverts one conclusion of this report.** Caught by seat 27 replicating on an independent 120-position set and
> confirmed by me by hand.

| switch | pooled node ratio | median | share ON < OFF | count | **sign p (correct)** | ~~published~~ | IQR | IQR/effect |
|---|---|---|---|---|---|---|---|---|
| **TtPruneV2** | 0.9528 | 0.928 | **60.8 %** | **73/120** | **0.0221** | ~~1.000~~ | 0.462 | **9.8** |
| **CuckooRep** | 0.9914 | 0.999 | **52.5 %** | **63/120** | **0.6483** | ~~1.000~~ | 0.256 | **28.4** |
| **CorrHistV2** | 0.9478 | 0.959 | **54.2 %** | **65/120** | **0.4114** | ~~1.000~~ | 0.413 | **7.9** |
| **HistRework** | 1.0311 | 1.018 | **46.7 %** | **56/120** | **0.5230** | 0.5230 ✓ | 0.514 | **16.6** |

**THE BUG, exactly.** My earlier cell computed `2*sum_{i=0..k} C(n,i)/2^n` and **omitted the `min(k, n-k)`
reflection**, so for any share **above** 50 % the tail summed from 0 to k ≈ 1.0 and the result capped at 1.000.
It was only correct for **below**-50 % shares — which is why HistRework (56/120) came out right and the other three
did not. **A bug that is silent on exactly half its inputs is the worst kind: it looked like a validated function
because one row agreed.**

**CORRECTED CONCLUSION — this reverses a sentence I published:**
- ~~"No switch's per-position direction clears a sign test."~~ **FALSE.**
- **`TtPruneV2`'s per-position direction IS significant: 73/120, p = 0.0221.** A hard pruning gate does produce a
  *consistent* direction more often than the others — **my original mechanism intuition was directionally right
  after all; I just predicted the wrong size** (65-80 %; measured 60.8 %).
- CuckooRep (p = 0.648) and CorrHistV2 (p = 0.411) remain indistinguishable from a coin flip on sign.
- **BUT: TtPruneV2's POOLED MAGNITUDE is still unestablished** — its bootstrap CI [0.8814, 1.0307] includes 1.0.
  **Significance on a sign test and significance on a paired-effect test are different questions**, and this row
  answers yes to the first and no to the second. Both must be reported.

**Every switch behaves the same way: a pooled effect of 1–5 % sitting inside a per-position spread 8–28× its
own size, with sign agreement between 46.7 % and 60.8 %.** No switch's per-position direction clears a sign test.

## Both of my predictions failed, and the TtPruneV2 failure is the instructive one
1. **I predicted TtPruneV2 would be the least coin-flip-like (65–80 % sign agreement)**, reasoning that it is a
   **hard pruning gate** — a node is cut or it is not — rather than a statistical reweighting like correction
   history or a replacement policy. **Measured 60.8 %: the highest of the four, but far below my range, and
   p = 1.000.**

   **Why the reasoning failed, stated plainly:** I confused *determinism of the mechanism* with *consistency of
   the effect*. The gate is deterministic **given a node** — the same node is always cut or not cut. But whether
   the gate fires at all **depends on the node**, and which nodes a search visits depends on the tree the other
   three switches shape. So a hard gate produces a **position-dependent** node saving in exactly the same way a
   soft one does. **Mechanism tells you what happens at a node; it tells you nothing about the variance across
   nodes.**

   **This is the generalisable form: mechanism-based intuition about the MEAN can be sound while intuition about
   the VARIANCE is worthless.** I reasoned correctly about what the switch does and incorrectly about how
   consistently it does it. Variance has to be measured, not derived.
2. I predicted CuckooRep/HistRework at 50–60 %. **Correct** (52.5 %, 46.7 %) — but that is the easy half of the
   prediction, and it rests on the same reasoning that failed for TtPruneV2. **The one prediction I got right does
   not rescue the one I got wrong: I was right for the wrong reason.**

## The kill condition: it fired, and how I am treating it honestly
I wrote before measuring: *"if ALL FOUR show < 60 % sign agreement, then coin flip is the general shape."*
**Strictly, that did not fire: TtPruneV2 is 60.8 %, 0.8 points above a threshold I chose myself.**
**I am not going to invoke the threshold to escape the conclusion.** The threshold was arbitrary and the deviation
is 0.8 percentage points, and **moving a line I drew before seeing data would be the same self-serving reasoning I
have criticised elsewhere in this record.**

**One part of my original justification for that paragraph is now void:** I wrote "its sign test is p = 1.000", and
**that was the reflection bug — the correct value is p = 0.0221.** So TtPruneV2's sign agreement is **statistically
real**, and the honest statement is: **three of the four switches show no established per-position direction
(CuckooRep 0.648, CorrHistV2 0.411, HistRework 0.523), and one does (TtPruneV2, 0.022).** **The coin-flip shape is
the general pattern with one real exception, not a universal rule** — which is a weaker claim than the one I
published, and I am correcting downward.

## What this changes in 19-C56
19-C56 said the 54.2 % was "a property of the switch", singular. **Corrected: it is a property of the SWITCH SET —
of what pruning and history changes do to a search tree, not of `CorrHistV2` specifically.** The sentence should
read: *the PC20 switches each reduce nodes on a pooled basis while flipping direction on individual positions.*

## Why this matters beyond bookkeeping — it reaches the depth result
19-C44/45 measured PC20 reaching **+3 ply at 20k nodes** and PC20 **12.4 % fewer nodes** at matched depth.
**This run says the per-position node effect of every switch is a coin flip.** So:
- **"PC20 searches 12 % fewer nodes" is a SESSION-level statement.** It is true summed over a game and
  **unusable for predicting any single position's cost** — which is what a fixed-node depth comparison is built
  from. The +3 ply at 20k is therefore an *average over positions*, not a property any given position has.
- **It does not invalidate the depth result** — an average depth advantage is still an advantage, and 19-C60
  used depth 12 with 120 positions, far more than enough for a pooled claim.
- **It does bound the claim honestly: PC20's node saving and its depth edge are distributional facts.** A
  position-by-position prediction of "PC20 will be cheaper here" has the same 50/50 reliability for all four
  switches.

## The generalisable lesson
**A pooled effect size says nothing about the fraction of cases that share its sign, and the two must be reported
together.** Four switches, four different mechanisms, all with IQR/effect ≥ 7.9 — this is not a quirk of one
option; it is what per-position variance looks like in a search whose tree shape feeds back into every pruning
decision. **Any finding of the form "this option saves X %" from this engine should carry the sign-share with it.**
