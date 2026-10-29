# IDEA_SOURCE: Opus round 5A (gate-ready singles)

This job adds no new search or evaluation idea. It audits, guards, smoke-tests and packages options that already
exist on `forge-bundle-int` b7c17722; their sources are recorded where they were introduced:
- CorrMargins (Opus O5), CorrExt (Opus O8), CorrHistPlus (Opus C2), CuckooRep (Opus C6): `opus_round1/*/IDEA_SOURCE.md`
  and `opus_r3/R3-1/IDEA_SOURCE.md`.
- NetScale (Sol S41), HistRework (Astra A1): `opus_r3/R3-1/IDEA_SOURCE.md`.
- CorrHistV2 / LmrTableV2 / TtPruneV2 and the B1-B4 presets (Fable FB2-J3): `BUNDLES.md` (IDEA_SOURCE section).

Engineering ideas used here (tooling, no engine code copied):
- One `info string` line that echoes the effective non-default settings at search start: common practice in UCI
  engines and match runners for reproducible logs (UCI protocol, `info string`: https://www.shredderchess.com/download/div/uci.zip,
  "info string <str>"). Implementation is my own.
- Smoke games as a crash/illegal-move/time-loss screen before SPRT, not as a strength test: standard engine-testing
  practice (fastchess/cutechess "-recover"/crash reporting; Chess Programming Wiki "Engine Testing",
  https://www.chessprogramming.org/Engine_Testing). The runner `smoke.py` is my own (python-chess for move legality).
- SPRT [0,10] normalized Elo, game cap 3000: the Forge gate convention given in the job spec; bounds math in
  `fable_fb2/j6` (GATE_BOUNDS.md on fable-fb2-j1).
- Exposing tunable constants as advertised UCI spin options so fastchess `-strict` and SPSA tuners accept them:
  existing Forge practice (R3-4, `tools/spsa/README.md`); SPSA itself: Spall 1992, "Multivariate stochastic
  approximation using a simultaneous perturbation gradient approximation", IEEE TAC 37(3).
