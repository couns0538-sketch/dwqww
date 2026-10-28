# O4 idea sources (UCI PureNnue: the network as the whole evaluation)

Ideas only. All code in this job is our own; no code was copied from any engine or trainer.

## Primary source
- **OPUS_TOP_ENGINES_2025_2026.pdf** (Opus's own research report, attached to the round-2 prompt):
  - section 7, table "NNUE architecture for small/medium nets", row "Pure NNUE (no hand-crafted base)": the net
    predicts the whole score, not a correction to the hand-crafted eval; status NEW for Forge;
  - section 10 "Hybrid hand-crafted eval + NNUE": once the net is strong the hand-crafted eval is mainly a speed
    cost; test to run: "train a pure NNUE of the same width on the same data with the same target, and play it
    against the residual version"; keep at most cheap drawish-material scaling;
  - recommendation A.3 "Pure NNUE: remove the hand-crafted eval from the hot path" (test plan row G-A5).

## Sources cited by the report (concept level)
- Stockfish PR #4674 "Remove classical evaluation" (2023), https://github.com/official-stockfish/Stockfish/pull/4674 :
  removing the frozen hand-crafted evaluation cost "roughly 2 Elo" in three 100,000-game tests.
- Stockfish discussion #4678, https://github.com/official-stockfish/Stockfish/discussions/4678 (a small net took
  over the hand-crafted evaluation's remaining role).
- Chess Programming Wiki, "Stockfish NNUE", https://www.chessprogramming.org/Stockfish_NNUE (the 2020 hybrid
  hand-crafted + NNUE evaluation as a temporary step).
- tcheran and akimbo changelogs (as summarised in the report): pure (768 -> N) x 2 nets replacing a hand-crafted
  evaluation.

## What we took and what we did ourselves
- Concept: train the network on the whole target (teacher score / game result blend) instead of the residual
  over the hand-crafted evaluation, and skip the hand-crafted evaluation at run time.
- Our own design: the trainer option `--pure` on the existing v3b trainer (whose non-residual model already
  computes `logit = net(x)`), optional `.hce` input for pure runs, the v2 export with the C4 header's residual
  flag cleared, and the engine rule that the header flag and UCI PureNnue must agree (fail-loud otherwise), so
  the hand-crafted evaluation is skipped exactly when PureNnue is true.
- Not done here (possible follow-up, own option and gate): the report's "cheap drawish-material scaling" of the
  net output.
