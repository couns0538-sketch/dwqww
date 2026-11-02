# R13 Phase 7 - fit the E3 eval post-processing values - DONE (fit run after the CR R13 fixes) - UNPROVEN
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

## Fit run (2026-11-01, after the CR fixes)
- raw_eval compiles on the lock tree d4f4312: 0 warnings (logs/build_raw_eval.log), exe ebd27774...
- Data: 6 AL1 gate PGNs (gateR11H2H_B_winner_vs_AL1plain833c, gate_sf26bundle14_vs_AL1, uhoR12_bundle_w21pt_7d50_vs_AL1lp,
  uhoR5A1_corrhistplus4_lp442f_vs_AL1lp, uhoR5A2_corrext1_lp442f_vs_AL1lp, uhoSF26bit1_razor_e417_vs_AL1lp): 11,888 games
  (2 duplicate games skipped), 495,015 positions (every 3rd ply from ply 16, not in check); split by game: 20% held out.
  Hashes: logs/inputs.sha256. Full numbers: logs/fit_e3.json.

| set (s = EvalMatScale, k = EvalOptimism, d = EvalRule50Damp) | held-out log-loss | minus OFF, 95% CI (game bootstrap, 2000) |
|---|---|---|
| OFF (0, 0, 0) | 0.569080 | - |
| hand (12, 40, 30) | 0.568578 | -0.000502 [-0.001484, +0.000339] (not separated from OFF) |
| hand MatScale 12 only | 0.570056 | worse than OFF |
| fitted EvalMatScale only | 0 = OFF | 0 (any MatScale > 0 fits worse) |
| fitted EvalRule50Damp only | d = 60 (range maximum) 0.566942 | -0.002138 [-0.003138, -0.001283] |
| fitted EvalOptimism only (static approximation: WEAK evidence) | k = 150 (range maximum) 0.567371 | -0.001708 [-0.002351, -0.001144] |
| fitted all three | (0, 150, 60) 0.565639 | -0.003441 [-0.004849, -0.002249]; vs hand -0.002939 [-0.003389, -0.002545] |

Reading (no Elo claim; calibration of the static eval is not playing strength, only a gate decides):
- EvalRule50Damp: the fit prefers the strongest damping the option allows (60 = range maximum, so the optimum may lie beyond
  the range); clearly better calibrated than OFF and than the hand value 30 on held-out games.
- EvalMatScale: the data do not support it at any value (fit = 0); the hand value 12 calibrates worse than OFF.
- EvalOptimism: fitted at its range maximum, but the static fit replaces the search's previous-iteration root score by the
  position's own eval, so it is WEAK evidence (CR R13) - keep the hand value unless a gate says otherwise.

## Candidate lines (same E3 exe: the fitted values are inside its option ranges; no rebuild)
1. `setoption name EvalRule50Damp value 60` (fitted; instead of the hand line 30).
2. Optional, weak evidence: `setoption name EvalOptimism value 150` (instead of 40).
3. EvalMatScale: no fitted candidate (the fit says 0); the hand line 12 is not supported by these data.
E3 gate results were checked first: none of the E3 options had a gate (no RUN_INFO uses them), so none was H0.
