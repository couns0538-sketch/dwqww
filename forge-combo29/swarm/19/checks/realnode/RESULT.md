# 19-C56 — re-checking 19-F32's "CorrHistV2 saves 4.3 % of nodes" on real positions: the magnitude SURVIVES, the claim's generality does not

## The claim under test
**19-F32**: "`CorrHistV2` ... `bench 13` gives **587,276 nodes with it on and 613,774 with it off**
— deterministic, identical in 3 reps (**so it saves 4.3 % of nodes**)". Measured on **bench 13 only**.
19-C55 showed bench gets the *sign* of the broader PC20 node effect wrong on 2 of 3 benches, so a bench-13
*magnitude* had to be re-checked.

## The re-check
PC r15, Threads 1, Hash 16, **depth 12**, real positions (`their_600.fens` first 120), **only `CorrHistV2`
toggled** with all other PC20 options held constant, interleaved, fresh process per search, all 120 pairs reaching
depth 12.

| | nodes | ratio |
|---|---|---|
| bench 13: ON | 587,276 | |
| bench 13: OFF | 613,774 | **0.9568 → saves 4.3 %** |
| **real, n=120: ON** | 7,127,974 | |
| **real, n=120: OFF** | 7,520,256 | **0.9478 → saves 5.2 %** |

**Per-position ratio: min 0.483 | Q1 0.767 | MEDIAN 0.959 | Q3 1.180 | max 2.582; mean 1.021; sd 0.358.**

## Verdict: SURVIVES on magnitude, FAILS on generality
- **The pooled saving is 5.2 % on real positions vs 4.3 % on bench 13 — the same effect size.** So 19-F32's
  number is **not** an artefact of bench, unlike 19-C35's per-node figure. **This is a case where bench transferred
  correctly, which is worth recording precisely because it contrasts with 19-C35 and 19-C55.**
- **But the claim "saves 4.3 % of nodes" reads as a property of the switch, and it is a POOLED property only.**
  **Only 54.2 % of positions (65 of 120) show ON using fewer nodes** — barely better than a coin. The Q1→Q3 range
  is **0.767 to 1.180**, i.e. the interquartile spread is **28× the effect size**. For any single position the
  switch is as likely to cost nodes as save them.
- **And it changes the move in 20.8 % of positions (25 of 120)**, consistent with 19-F33's 22.0 % — so the node
  saving is not a free efficiency gain; it is a different search.

## The trap I fell into on the way (kept in the record)
My **6-position smoke test** gave a pooled saving of **21.5 %** (ratio 0.7848) — five times the true figure — and I
had begun writing "the magnitude is off by 5×" before the full run. **It was small-sample noise of exactly the kind
that produced 19-C52's 7-of-14.** The full n=120 run gives 5.2 %, which agrees with bench. **Recorded because the
smoke number was more dramatic than the truth and I nearly published it.**

## What this means for the audit of bench-based claims
Bench-measured node magnitudes are **not uniformly invalid** — 19-F32 transfers (4.3 % → 5.2 %). What fails is:
1. **per-node cost** (19-C35: 1.2 % bench vs 7 % real) — bench is 6× too optimistic;
2. **the sign of the aggregate PC20 node effect** (19-C55: +14.5 %, −10.6 %, +8.7 % across benches 11/13/16);
3. **any reading of a pooled magnitude as a per-position property** — true for 19-F32 regardless of bench.

**So the corrected rule is narrower and more useful than "never use bench for magnitudes": use bench for the
DIRECTION and for POOLED effect sizes of a single isolated toggle, but verify (a) per-node cost, (b) anything about
the aggregate PC20 set, and (c) always report the per-position spread, because a pooled ratio can hide a coin flip.**
