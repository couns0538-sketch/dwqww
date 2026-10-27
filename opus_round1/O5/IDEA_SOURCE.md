# O5 idea sources (UCI CorrMargins, test plan G-B3)

Ideas only. All code, formulas and constants in this job are our own; no code was copied from any
engine (in particular none from Stockfish, GPL-3).

## Primary source
- **OPUS_TOP_ENGINES_2025_2026.pdf** — Opus's own research report "What the Best Chess Engines (2025-2026)
  Do Best, and Which Ideas 'Forge' Should Adopt" (attached to the round-2 prompt, 2026-10-26):
  - Section 1 (search pruning) table row "Correction size used as 'complexity' in futility margins":
    *when the correction tables say the static eval is unreliable here, require a bigger margin before
    futility-pruning*; status NEW, expected +1-3, "Trivial; one extra term".
  - Section 3 (correction history family) row "Correction as a complexity proxy": *feed correction
    magnitude into LMR and RFP margins* (CPW "Additional uses"; futility version SF PR #5748).
  - Recommendation B.10: "Correction size as a complexity term in pruning margins. Widen futility (and
    possibly RFP) margins when the total correction is large, because the static eval is less reliable
    in those positions."
  - Test plan row G-B3 (OPUS_TEST_PLAN.md): "Correction-size pruning margins", srand 1162618901.

## Public sources cited by the report (concept only; checked 2026-10-27)
- Stockfish PR #5748 "corrplexity for futility pruning" (daniel-monroe, closed into master 2025-01-05):
  a correction-history term in the futility pruning margin. STC passed (545,504 games, bounds [0,2]),
  LTC passed (125,994 games, bounds [0.5,2.5]). https://github.com/official-stockfish/Stockfish/pull/5748
- Stockfish PR #5727 "Adjust LMR with correction history" (xu-shawn, closed into master 2024-12-22): the
  correction size as a gauge of positional instability lowers the reduction. STC 109,216 games and LTC
  66,918 games passed. https://github.com/official-stockfish/Stockfish/pull/5727
- Chess Programming Wiki, "Static Evaluation Correction History", section "Additional Uses": correction
  history as a proxy for position complexity, used in search techniques such as LMR and RFP.
  https://www.chessprogramming.org/Static_Evaluation_Correction_History

## Forge history checked (7_history, rule 8)
- Idea board P7 "LMR reduction relief from the size of the eval correction" (correction-magnitude LMR,
  whole-ply `r -= 1` above a threshold): gate G16 (`LmrCorrThreshold=30` on the ep10 base) ended
  "cap with no decision" (-0.69 +- 10.01). The board's lesson: "whole-ply r-=1 cannot be calibrated
  (T=40 triggers 50% at d20, +69% nodes); parked unless rewritten as a fractional/depth-scaled term."
  O5's LMR term is that rewrite: a share of the reduction proportional to |correction| (CorrLmrPct
  percent per 64 cp, rounded down), so at the default weight 25 only reductions of 4 plies or more are
  cut, and only at large corrections (measured: 0.2-3.6% of reduced moves at d13-d20 for weight 25,
  versus 17-41% for the whole-ply rule at 30 cp; logs/correction_size_distribution.log). O5 also adds the
  RFP, quiet-futility and null-move terms, which P7 did not have, and is one option for the whole
  bundle (G-B3).

## What is our own
- The measure |static_eval - raw_eval| (the correction actually applied at the node, 0 in check).
- The four margin functions in `include/forge/corr_margins.hpp` (AL1 s198 formula + a term linear in
  |correction|, rounded down; the LMR share capped at the reduction) and their weights
  CorrRfpPct 50, CorrFutilityPct 100, CorrNullMovePct 50, CorrLmrPct 25, chosen from our own
  measurements (bench and a 50-position sweep, `node_sweep.py`, logs/calibration_*.log) so that the
  fixed-depth node count stays inside the +10% pre-gate band.
- The code layout: a second instance of alphabeta.inc selected once per iteration, with its own copy of
  lmp_threshold so that the default search stays instruction-identical to AL1 s198.
