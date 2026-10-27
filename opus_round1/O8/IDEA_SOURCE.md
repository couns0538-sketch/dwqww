# O8 idea sources (UCI CorrExt, test plan G-C5)

Ideas only. All code, formulas and constants in this job are our own; no code was copied from any
engine (in particular none from Stockfish, GPL-3).

## Primary source
- **OPUS_TOP_ENGINES_2025_2026.pdf** — Opus's own research report "What the Best Chess Engines (2025-2026)
  Do Best, and Which Ideas 'Forge' Should Adopt" (attached to the round-2 prompt, 2026-10-26):
  - Key findings / time-control scaling: "Stockfish's 'correction-history quad extensions' measured
    -4.40 +- 1.4 Elo at STC but passed two very-long-TC SPRTs (SF PR #5767)."
  - Section 1 (search pruning, reductions and extensions) table row "Correction-adjusted extension
    margins ('quad extensions')": *make double/triple extension thresholds depend on correction
    magnitude, allowing extensions beyond triple*; expected gain "Negative at 10+0.1", "Loses at short
    TC", status "NEW, avoid" for a 10+0.1-only gate.
  - Test plan row G-C5 (OPUS_TEST_PLAN.md): "Correction-history extensions (SF 'quad ext')", gated at
    40+0.4 as the primary gate ("lost at STC in report"), srand 113016036.

## Public source cited by the report (concept only; checked 2026-10-27)
- Stockfish PR #5767 "Introduce Correction History Quad Extensions" (Viren6, closed into master
  2025-01-12): an extension level above triple tied to correction history, and double/triple
  extension margins that take the correction history into account. STC -4.40 +- 1.4 Elo (60,000 games);
  two VVLTC SPRTs passed (35,736 games, bounds [0,2]; 36,394 games, bounds [0.5,2.5]).
  https://github.com/official-stockfish/Stockfish/pull/5767
- Chess Programming Wiki, "Static Evaluation Correction History", section "Additional Uses":
  correction history as a proxy for position complexity in search techniques.
  https://www.chessprogramming.org/Static_Evaluation_Correction_History

## Forge history checked (7_history, rule 8)
- No correction-dependent extension was tried before (idea board, gate results G1..G125; the only
  correction-magnitude search change, P7 correction-magnitude LMR / gate G16, is a reduction rule and
  belongs to O5 / G-B3). Forge's singular extension already has double extensions (margin 24 cp, at
  most 7 per path via SearchStack::double_extensions) and negative extensions; O8 builds on those.
- Related, different ideas on the idea board: E28 (SingularMargin=1, i.e. more singular extensions at
  every node) "loses"; P22 SingTtPv proposed a DoubleExtMargin knob to make double extensions *rarer*
  (no gate result recorded). O8 keeps the singular margin and the default double margin, and extends
  more only where |correction| is large, with the extra plies per path capped as in AL1 s198.

## What is our own
- The measure |static_eval - raw_eval| (the correction actually applied at the node, 0 in check).
- The rule in `include/forge/corr_ext.hpp`: the AL1 s198 double margin 24 cp minus CorrExtDoublePct
  percent of |correction| (floored at 0); a *triple* extension (Forge has no triple, so this is the
  analogue of the extra "quad" level) at |correction| >= CorrExtTripleCorr when the singular score is
  more than CorrExtTripleMargin below the singular beta; and one per-path budget for all extra plies
  (a double costs 1, a triple 2; CorrExtBudget 7 = the AL1 s198 allowance of 7 doubles), so the depth
  added along any path is bounded exactly as in AL1 s198.
- The defaults 12 / 48 / 100 / 7, chosen from our own measurements (a probe of the singular-extension
  statistics by |correction| and bench / 50-position node sweeps, logs/calibration_*.log) so that the
  fixed-depth node count stays inside the +10% pre-gate band at d13 / d16; stronger settings
  (e.g. 25 / 32 / 100) grow the d20 tree by +25% or more.
- The code layout: a second instance of alphabeta.inc selected once per iteration, with its own copy of
  lmp_threshold so that the default search stays instruction-identical to AL1 s198.
