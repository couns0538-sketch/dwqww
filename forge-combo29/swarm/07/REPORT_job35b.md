# REPORT — seat 07, job 35b: the per-option table at all 200 positions — and a correction to the 40-position one

## What was asked / the answer / how sure

**Asked:** extend the S14 + one-PC20-option table from the first 40 positions to all 200, so the
totals are comparable to the four legs and show exactly which option carries the interaction.

**Answer:** done, and **the larger sample reverses two signs and moves most of the weight onto a single
option.** `TtPruneV2` alone is **85 %** of PC20's entire effect (−1,002,190 of −1,184,901). On 40
positions it had looked like `TtPruneV2` merely outweighing `CorrHistV2`; on 200 positions
`CuckooRep` and both `HistRework` levels are *also* negative, so the bundle is not a cancellation.

**How sure:** high for the 200-position numbers — baseline is the same 9,500,069 used by the four
legs, so they are directly comparable, and every run is a fresh process at Threads 1, Hash 16.
**The 40-position table is withdrawn as a basis for defaults**; it is kept only as an example of a
sample too small to rank options.

## The table (PC build, depth 12, Threads 1, Hash 16, all 200 positions)

| configuration | sum | Δ vs S14 | % | share of PC20's −1,184,901 |
|---|---|---|---|---|
| S14 | 9,500,069 | — | — | — |
| + **TtPruneV2** | 8,497,879 | **−1,002,190** | **−10.5 %** | **85 %** |
| + CorrHistV2 | 9,752,004 | +251,935 | +2.7 % | — |
| + HistRework 3 | 9,371,695 | −128,374 | −1.4 % | 11 % |
| + HistRework 2 | 9,442,626 | −57,443 | −0.6 % | 5 % |
| + CuckooRep | 9,446,599 | −53,470 | −0.6 % | 5 % |
| + MateAlphaGuard | 9,500,069 | **0** | 0.0 % | 0 % |
| + OwnBook false | 9,500,069 | **0** | 0.0 % | 0 % |
| **all six (PC20)** | **8,315,168** | **−1,184,901** | **−12.5 %** | 100 % |

(The share column sums past 100 % because `CorrHistV2` pushes the other way; the point is the ranking,
not the arithmetic.)

## What this says to the owner, in one line

**`TtPruneV2` is doing almost all of the work, and it is the only option whose effect is large enough
to matter on its own.** If the owner is choosing defaults from node counts alone, `TtPruneV2 true` is
the one that earns its place; `CorrHistV2` costs 2.7 % and must be justified by strength (a games
question, not measured here); `CuckooRep` and the two `HistRework` levels each contribute about half a
percent, which is within the range where a node count is not a strong argument either way;
`MateAlphaGuard` and `OwnBook false` are behaviour switches that cost nothing here.

## The correction I have to make to my own 40-position table

| option | 40 positions (07-C31) | 200 positions (this job) |
|---|---|---|
| CuckooRep | **+72,364 (+4.3 %)** | **−53,470 (−0.6 %)** |
| HistRework 2 | +517 (+0.0 %) | **−57,443 (−0.6 %)** |
| HistRework 3 | +15,655 (+0.9 %) | **−128,374 (−1.4 %)** |
| TtPruneV2 | −163,541 (−9.7 %) | −1,002,190 (−10.5 %) |
| CorrHistV2 | +208,947 (+12.4 %) | +251,935 (+2.7 %) |
| all six | −138,940 (−8.2 %) | −1,184,901 (−12.5 %) |

Three of six options **changed sign** between 40 and 200 positions. The percentages also moved a lot,
because 40 positions is a small and unrepresentative slice: `CorrHistV2`'s drag fell from +12.4 % to
+2.7 % of the respective baselines, and `CuckooRep` went from a 4.3 % cost to a 0.6 % saving.

Why this happened, as best I can tell without further work: the first 40 positions of set O are
dominated by early opening positions where a few trees are enormous, so a change that reshapes those
trees dominates the total. This is exactly the trap of measuring an option's effect on a small slice,
and I walked into it. **Anyone quoting a per-option node percentage from this seat should use the
200-position column.**

## Findings

**07-C32** in FINDINGS.md, which explicitly corrects 07-C31.

## Suspicions, not proven

- Whether `TtPruneV2`'s −10.5 % is a genuine speed win or a sign of over-pruning that loses strength.
  A 10 % node reduction from a pruning switch is plausible and also exactly what a *too*-aggressive
  prune looks like. Only games can separate them, and I did not play any.

## What I did NOT do

- Did not play games, so no strength claim for any option.
- Did not test option pairs (e.g. TtPruneV2 + CorrHistV2) to look for interactions between options;
  the four-leg result showed build×settings is an interaction, and option×option could be too.

## What I am NOT sure about

- Whether 200 positions is still too few to rank the three sub-1 % options. Their signs are stable
  across the full set in a way the 40-position signs were not, but I would not quote a precise
  percentage for any of them.

## Times

See job35/stamps.txt.
