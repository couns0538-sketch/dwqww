# IDEA_SOURCE — S41 eval-scale check + NetScale (UCI, default 100 = OFF)

- **The job**: Sol's S41 spec, `F:\opus_scratch\sol_inventory_17aa0cae.json` `jobs[]` id S41 (Sol's branch
  `17aa0cae`, inventory `forge_sol_all_jobs_inventory_20261026.json`): compare the static-eval spread of e48f006,
  f029 and s198 against h256_e12 on 10k fixed positions (WAC300 + self-play) with |eval| quantiles and a robust
  slope fit; propose one OFF-default `NetScale` option. Sol never started S41 (no S41 files on `17aa0cae`).
- **Crew idea**: Engine Strength, round 2026-10-25 12:15 ("S34 (Sol) Eval-scale check for a new lock net",
  lock archive `7_history/ideas/crew_ideas_older/round_20261025_1215/Engine_Strength_ideas_20261025_1215.md`), rework
  14:15 ("run the scale check first on whichever net becomes the lock"); idea board row 7 "NetScalePct=90"
  (`7_history/ideas/FORGE_IDEA_BOARD.md`); improve prompt EVAL-1 ("a NetScalePct", `00_FORGE_IMPROVE_PROMPT_20261026_1039.md`).
  Reason given there: the pruning margins (RFP, futility, razoring, ...) were tuned on h256_e12's eval scale.
- **NetScale**: a general technique (a linear rescale of an evaluation function's output; CPW "Evaluation"). Own
  code: `include/forge/net_scale.hpp` (`apply`), one hook in `Worker::static_evaluate` (`src/search.cpp`), one UCI
  option (`src/uci.cpp`). An earlier box build advertised a `NetScalePct` (omni_eval expose exe, 2026-10-24); its
  source is not on the PC and was not used or looked at.
- **Statistics**: least-absolute-deviation regression through the origin (= weighted median of ratios; Laplace /
  Edgeworth), Theil-Sen estimator (Theil 1950, Sen 1968), Huber M-estimator (Huber 1964), a geometric-mean
  (reduced-major-axis style) combination of the two LAD directions for a symmetric scale, percentile bootstrap.
  Own Python (numpy) implementation, `tools/evalscale_20261027.py`.
- **Harness**: `tools/evalscale_dump.cpp`, own code, same build pattern as the lock archive's own `5_nnue/tools/nnue_check.cpp`
  (network as `nnue_weights.inc` next to a copy of `src/nnue.cpp`) and as `opus-sol-S21`'s engine-parity tool.
- **Test**: `tests/net_scale_tests.cpp` uses the `SearcherTestProbe` friend hook the lock's own
  `tests/runtime_psqt_tests.cpp` uses, with an independent oracle.
- No code, tables or tuned constants from any other engine.
