# PREDICTION - committed BEFORE measuring (19-C60: is the coin flip general to the PC20 switches?)

## What I am testing
19-C56 found `CorrHistV2` saves **5.2 % of nodes pooled** but uses fewer on only **54.2 % of positions**
(65/120), IQR 0.767-1.180 = **28x the effect size**. I called that "a property of the switch".

**That was one switch out of four.** If the other three are bimodal in the same way, then **every "PC20 saves
~12 % of nodes" statement is a session-level statement only**, and the depth-at-fixed-nodes result (19-C44/45)
inherits the same caveat. If they differ, the coin-flip shape is specific and should not be generalised.

Switches to test, one at a time, PC r15, all other PC20 options held constant:
  TtPruneV2, CuckooRep, HistRework(2 vs 0/1 - use off-vs-default), CorrHistV2 (the 19-C56 baseline, re-run for
  a like-for-like comparison on the same 120 positions and depth).

## My prediction
1. **All four will show a pooled node change smaller than their per-position spread** — I predict IQR/effect > 5
   for all four. Reason: each switch gates a pruning or history decision that fires position-dependently.
2. **TtPruneV2 will be the LEAST coin-flip-like** (highest fraction of positions sharing the sign), because it is
   a hard pruning gate (a node is cut or not) rather than a statistical reweighting. **I predict 65-80 % of
   positions agree** for TtPruneV2, against ~54 % for CorrHistV2.
3. **CuckooRep and HistRework will look like CorrHistV2** (50-60 % sign agreement).
4. **Kill condition for my framing:** if ALL FOUR show < 60 % sign agreement, then "coin flip" is the general shape
   and I should say so for the whole set rather than for one switch.

## What each outcome means
- **Mixed (>65 % for TtPruneV2, ~54 % for the rest)** -> the shape is switch-specific, and my C56 sentence should
  name CorrHistV2 rather than "the switch".
- **All <60 %** -> general: any per-position node prediction from these options is unreliable, and the 12 % figure
  needs the session-level qualifier on every use.
- **All >70 %** -> C56's 54.2 % was itself a small-sample artefact at n=120 and I should say so.
