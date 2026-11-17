# NOTE_bench_bias_is_patch_specific.md — the final form of the bench rule

**Status: FINAL. Third revision, and the first that is falsifiable rather than hortatory.**

---

## The rule

> **`bench`'s bias relative to real positions is PATCH-SPECIFIC, not directional.**
> It may understate, match, or overstate. There is no blanket rule about which way it errs.
>
> **Operational consequence: if the number matters, measure it on real positions once.**

That is the whole rule. Everything below is why the two earlier versions failed and what the evidence is.

---

## Why the first two versions were wrong

| version | the claim | how it failed |
|---|---|---|
| **1** | "never use `bench` for magnitudes" | **Too broad.** 19-C56: 19-F32's `CorrHistV2` node saving measured **4.3 % on bench 13** and **5.2 % on real positions** — a bench magnitude that transferred correctly. Following version 1 would have told seats to **discard a valid result.** *Being wrong in the cautious direction is still being wrong.* |
| **2** | "`bench` understates per-node cost" (≈6×) | **Wrong as a generalisation.** It was inferred from **one** patch (19-C35: 1.2 % on bench vs 7 % real). 19-C58 tested a **different** patch and found the opposite: prefetch measured **9.43 % on bench 13** and **9.80 % on real positions** — bench was **accurate**. The bias had no direction; it had a patch. |
| **3 (FINAL)** | **bias is patch-specific** | Falsifiable: it predicts that for *some* patch, bench and real positions will agree closely, and for another they will diverge in either direction. 19-C35 (diverge, bench optimistic) and 19-C58 (agree) are both instances, and a future counter-example would refute it. |

**Each revision was forced by a measurement, not by a preference for caution.** That sequence is the useful record: version 1 was corrected by a case where bench worked, version 2 by a case where bench's "known" bias did not appear.

---

## The evidence in one table

| finding | patch | bench figure | real-position figure | verdict |
|---|---|---|---|---|
| **19-C35 / 19-C53** | PC20 option set, per-node cost | **1.0119** (+1.2 %) | **median 1.071** (+7.1 %) | **bench UNDERSTATED ~6×** |
| **19-F32 / 19-C56** | `CorrHistV2` alone, node count | 0.9568 (−4.3 %) | **0.9478 (−5.2 %)** | **bench MATCHED** |
| **19-F10 / 29-C4 / 19-C58** | NNUE column prefetch, per-node | **1.0943** (+9.4 %) | **1.0980 (+9.8 %)** | **bench MATCHED** |
| **19-C55** | aggregate PC20 set, node *sign* | **+14.5 % / −10.6 % / +8.7 %** across bench 11/13/16 | **−9.1 %** | **bench got the SIGN wrong on 2 of 3 benches** |

**Three patches, three different relationships between bench and reality.** That is the evidence for "patch-specific", and it is why no directional rule can be right.

---

## What `bench` remains valid for — unaffected by this rule

These do not depend on the position distribution at all, so the bias question does not arise:

- **the four honesty pins** (by definition — that is what they are for);
- **determinism** and reproducibility checks;
- **ablation DIRECTION** (the sign of a change), which 19-F26 shows explicitly **varies by bench**, so a bench
  measurement of direction is a *conservative* test;
- **structural counters** — call counts, probe counts, hit-slot distributions (19-C19, 19-F42), which are
  properties of the code path, not of the tree shape.

## What requires a real-position measurement

- **per-node cost**, in either direction;
- **aggregate node or time effects of the PC20 set** (19-C55: the sign flips across benches);
- **any magnitude that will be quoted to the owner as a speed or node figure** — measure it once on real positions,
  because bench cannot tell you which way it will be wrong.

## One further distinction this forced
**A pooled ratio is not a per-position property.** 19-F32's 5 % pooled saving holds on only **54.2 %** of positions
(IQR 28× the effect size), so it is true of a session and useless for predicting a single position. **That is a
property of the switch, not a defect of bench, and more data will not remove it.** Reporting the per-position
spread is now part of the practice, not an optional nicety.
