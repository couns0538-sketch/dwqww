# R13 Phase 7 - fit the E3 eval post-processing values - IN PROGRESS, CR R13 = FIX (fixes below)
Branch `opus-r13-p7-e3fit` (from main). UNPROVEN: fitted values are proposals; only a gate decides.
- E3 gate results checked first: no gate RUN_INFO under F:\forge_push or D:\grok-pc-data\forge_push uses EvalMatScale /
  EvalOptimism / EvalRule50Damp / DrawJitter (2026-11-01), so none is H0 yet -> all three value options are fitted.
  DrawJitter is a draw-score randomiser (no value to fit by log-loss).
- E3 formulas (e3_evalpost_al1 src/search.cpp e3_post_eval, read from D:\grok-pc-data\opus30h_inputs\e3\e3_evalpost_al1_src.zip):
  optimism from the previous root score K*score/(|score|+120) weighted by material/M0, material factor
  1024 + s*(2M - M0)*1024/(100*M0), rule50 damping v -= v*D*min(clock,100)/10000, all on the raw static eval.
- Data (licence-clean): the crew's own gate PGNs under F:\forge_push (Forge vs Forge); positions via extract_positions.py
  (real halfmove clocks), raw lock evals via raw_eval.cpp (lock d4f4312 = E3's base), fit via fit_e3.py (80/20 split by game).
- Approximation stated up front: optimism depends on a search score; the static fit uses the position's own eval in its place.
Status: tools written; runs after the P3 SPSA frees CPUs 2-3.

## CR R13 (crew Code Review of 7d81f367) and fixes
| CR item | fix |
|---|---|
| raw_eval.cpp does not compile on the lock tree (d4f4312) | cause: Evaluator::refresh_runtime_psqt / evaluate_runtime are private on the lock (friend class Worker). Now the public Evaluator::evaluate_uncached + network, clamped - the exact reference formula of the lock's own tests/runtime_psqt_tests.cpp (lines 64-66: clamp(evaluate_uncached + nnue::evaluate, +-(MateInMaxPly-1)) == Worker::static_evaluate). Exits 1 on a FEN the board rejects. Compile proof: pending CPU (run log will be committed) |
| fit_e3.py exits 0 on bad input, no error bars | fails with exit 2 on: header mismatch, line-count mismatch, any non-integer / ERR eval, result outside {0, 0.5, 1}, material / clock out of range, fewer than 50 games or 2000 positions in either split. Error bars: game-level bootstrap (2000 resamples, seed 13701) of the held-out loss differences fitted - OFF, hand - OFF, fitted - hand and each single option - OFF, 95% percentile CI |
| dedupe PGNs before extracting | extract_positions.py skips a game whose result + start FEN + full move list was already seen in any file, counts the skips, and exits non-zero when nothing is extracted |
| fitted EvalOptimism = weak evidence | stated in the tool and in every report line: the static fit replaces the search's previous-iteration root score by the position's own eval |
