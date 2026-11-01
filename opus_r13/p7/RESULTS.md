# R13 Phase 7 - fit the E3 eval post-processing values - IN PROGRESS
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
