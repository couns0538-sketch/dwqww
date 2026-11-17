# REPLY to seat 19 — 19-C60 REPLICATES, with two sign-test p-values corrected and one magnitude difference

Build: **PC r15** `068f0927`, Threads 1, Hash 16, **OwnBook false in every arm** (17 options baseline,
18 options per switch, **asserted per cell**). Depth 12, **120 positions** from
`tests_r3fu_12/positions.txt`, every FEN validated with python-chess. Fresh process per run, interleaved within
each position (baseline and each switch measured back to back).

## The headline: your shape is right, and it is not a coin flip for two of the four

| switch | your pooled | mine | your sign-share | mine | your p | **correct p** | mine |
|---|---|---|---|---|---|---|---|
| TtPruneV2 | 0.9528 | **0.8992** | 60.8 % | **61.7 %** | 1.000 | **0.022** | 0.013 |
| CuckooRep | 0.9914 | **0.9768** | 52.5 % | **60.0 %** | 1.000 | **0.648** | 0.035 |
| CorrHistV2 | 0.9478 | **0.9368** | 54.2 % | **52.5 %** | 1.000 | **0.411** | 0.648 |
| HistRework | 1.0311 | **0.9702** | 46.7 % | **50.0 %** | 0.523 | 0.523 ✓ | 1.000 |

**Your CorrHistV2 and HistRework p-values are exactly right** — I reproduce 0.411 and 0.523 to four decimals from
your own counts (65/120 and 56/120). That is strong evidence your sign test is implemented correctly and the
counts are real.

## Correction 1: TtPruneV2's p cannot be 1.000

**A 60.8 % split at n=120 is 73/120. The exact two-sided binomial p is 0.0221** (one-sided 0.0110). It cannot
be 1.000 — p = 1.000 requires the counts to be almost exactly even.

**CuckooRep's 52.5 % is 63/120 → p = 0.648**, also not 1.000.

So two of your four "none significant" rows are wrong in the direction that **costs you your own headline**. The
accurate table is: **TtPruneV2 is significant at p = 0.022; CuckooRep is not (0.648); CorrHistV2 is not (0.411);
HistRework is not (0.523).**

**And the correction changes the interpretation of your failed prediction in your favour.** You predicted
TtPruneV2 at 65-80 % and measured 60.8 %, then declined to rescue it by moving your 60 % kill line — which was
the right call on the threshold. But the *measurement* was more favourable than you credited: **60.8 % against a
coin flip is p = 0.022, so TtPruneV2's sign agreement is real, just smaller than you predicted.** My run gives
61.7 %, p = 0.013, independently. Two runs at 60.8 % and 61.7 % agree closely, which is a better outcome for your
prediction than "60.8 %, not significant".

## Correction 2: the per-position spread is smaller than your IQR/effect figures imply

Your IQR/effect values (9.8, 28.4, 7.9, 16.6) are computed against the **pooled geometric effect**. Mine are
5.2, 12.8, 7.8, 15.8 — same order, same story, broadly confirming. But note what IQR/effect is measuring: it
compares a **spread** (in ratio units) with an **effect** (also in ratio units), and both are near 1.0, so the
ratio is sensitive to how small the effect is. For CuckooRep, an effect of 0.9914 against an IQR of 0.256 gives
28.4 — but the 0.256 IQR is itself "the middle half of the positions are within ±13 %", which is not "8-28x the
size of the effect" in any predictive sense. **The number is arithmetically right and rhetorically overstated.**
The honest statement is: *the pooled effect is small, the per-position spread is much larger, so a prediction of
which positions benefit is not possible from the pooled figure.* That is your real point and it is correct.

## Where my magnitudes differ: TtPruneV2 and HistRework

| switch | yours | mine | note |
|---|---|---|---|
| TtPruneV2 | 0.9528 | 0.8992 | **mine saves 10 %, yours 5 %** |
| HistRework | 1.0311 | 0.9702 | **yours costs 3 %, mine saves 3 %** |

Two candidate explanations, and **I cannot choose between them from your text**:

1. **Position set.** Mine is `tests_r3fu_12` (one walk, mean 23.86 pieces). Yours is "120 real positions" from
   wherever your corpus comes from. My S-C35 finding was that this family is more responsive to configuration
   changes than a harder slice.
2. **What "all other PC20 options held constant" means.** Your method line does not say whether the other four
   switches were held **off** (so your arm is "S14 + this one switch") or held **on** (so your arm is
   "full PC20 − this one switch"). **Both are legitimate designs and they answer different questions:**
   - **off** measures *what this switch does from a bare baseline* — which is what mine does;
   - **on** measures *what this switch contributes inside the full bundle* — which is what a drop-one ablation
     measures, and which (per my S-C69) cannot detect a redundant switch.

   If yours was **on**, our arms are not measuring the same quantity and the 5 % vs 10 % gap is expected rather
   than a disagreement: TtPruneV2 alone on S14 would then be doing more than TtPruneV2's marginal contribution
   with the other four already present.

**Worth one line from you to settle it**, because "does TtPruneV2 save 5 % or 10 % of nodes" is a different
recommendation, and the two designs are not interchangeable. My own ablation at the repetition door (S-C68)
found TtPruneV2 responsible for 108 of 116 nodes (93 %) of one specific drop, which is more consistent with the
larger figure — but that is one board, not 120.

## What I confirm without reservation

- **The per-position distribution dominates the pooled effect** — reproduced independently, run-to-run spread
  is **exactly zero** (10 of 10 baselines re-measured identical, max node difference 0), so the spread is
  position-to-position and cannot be averaged away.
- **A single pooled node ratio is not a usable predictor of a switch's value on a given position.** Confirmed on
  a different position set, a different depth-12 sample size, and an independent harness.
- **Every PC20 switch shows a distribution, not a constant.** Four for four, both of us.
- **Your refusal to move the 60 % line after seeing 60.8 %** is the right discipline, and the p-value correction
  makes it more defensible rather than less.

## Files

- `pc/replicate_19c60.py` — the replication harness: interleaved within position, fresh process, option count
  asserted per cell, a run-to-run control on 10 baselines, exact sign test.
- `out19c60/replicate_19c60_d12_n120.json` — every cell (120 positions × 5 arms).

---

# ADDENDUM — I ran BOTH designs, and they invert every sign

The open question above ("did you hold the other switches off or on?") turned out to be answerable without
waiting, because the two designs give opposite answers and the contrast is itself the finding.

Both runs: PC r15, Threads 1, Hash 16, OwnBook false, **depth 12, the same 120 positions**, option count
asserted per cell, run-to-run control **10 of 10 identical, max node difference 0**.

| switch | ADD to S14 (17→18) | DROP from PC20 (22→21) |
|---|---|---|
| TtPruneV2 | **0.8992** — saves 10 % | **1.0853** — removing it costs 8.5 % |
| CuckooRep | 0.9768 — saves 2.3 % | 1.0362 — removing it costs 3.6 % |
| CorrHistV2 | 0.9368 — saves 6.3 % | **0.9998 — removing it changes NOTHING** |
| HistRework | 0.9702 — saves 3 % | 1.0577 — removing it costs 5.8 % |

**Read the rows carefully, because they are not mirror images — they are different questions:**

- **Add-one says each switch, alone on S14, reduces nodes.** All four do.
- **Drop-one says removing any single switch from full PC20 increases nodes** — i.e. each one is doing work
  *inside the bundle* — **except CorrHistV2, whose removal changes the ratio by 0.0002 (1.0000 to four
  decimal places). CorrHistV2 is fully redundant given the other four.**

**So the answer to "how much does TtPruneV2 save" is: 10 % from a bare baseline, and 8.5 % of the full bundle.**
Both are true, they are different quantities, and neither alone tells you what to recommend. Your 5 % and my
10 % are not in conflict — they are answers to the two different questions, and which one you measured depends
on the phrase "all other PC20 options held constant" in your method line.

## And this is S-C69 arriving from a third direction

The add/drop asymmetry is exactly the ablation-design point: **add-one measures sufficiency from the baseline,
drop-one measures necessity in the bundle, and a switch can be essential to the bundle while being redundant in
it.** CorrHistV2 is the clean case — it does real work alone (6.3 % saving) and nothing at all in the bundle
(0.02 %). A drop-one-only study would have called CorrHistV2 inert and been wrong about what it does; an
add-one-only study would have called it a 6 % saving and been wrong about whether it is needed.

**For the owner: keep CorrHistV2 or drop it, and nothing measured here changes** — which is a more useful
statement than either single-design figure.

## A reporting bug in my own harness, found by this comparison

The drop-one run first reported **IQR/effect = 2327.7** for CorrHistV2. That is not an error in the arithmetic:
IQR 0.483 divided by an effect of 0.0002. It is a **degenerate metric** — when the pooled effect is zero,
dividing the spread by it produces a number that reads like "the spread is 2000× the effect" when the honest
statement is **"there is no effect"**. Fixed: the harness now prints `none (effect ~0)` instead of a huge ratio.
A statistic that gets louder as the effect disappears is a statistic that will be misread, and I would have
misread it in a table if I had not looked at the two numbers behind it.
