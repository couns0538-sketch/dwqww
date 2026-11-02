# R13 Phase 7 - fit the E3 eval post-processing values - DONE (R13 fit; R14: CR 129d440e items, wide refit: Rule50Damp optimum ~81 past the option max 60) - UNPROVEN
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

## R14 (2026-11-02): CR patch 129d440e, wider bounds, refit once - UNPROVEN
### CR patch 129d440e (`C:\Users\Administrator\qa_crfix_astra_r10\r13_patches\p7_e3fit_crfix.patch`)
It is CR's fix of 7d81f367 (applies cleanly there; not on cd9cb992, where my own CR fix cad3fe13 already changed the same
lines). Item by item: raw_eval "cannot open" check and the public eval path - already in cad3fe13 (CR uses
`Evaluator::evaluate`, mine `evaluate_uncached` + the network = the lock test's reference formula; CR box-checked the
public path = the private one 9985/9985); **ported now**: extract_positions.py skips and counts games the PGN reader flags
with errors (0 such games in these PGNs), fit_e3.py refuses to overwrite its output and flags values / slope on a bound;
CR's run rule (start at CPU <= 80 % and >= 8 GB free RAM, BelowNormal) and CR's note "the static optimism stand-in is a
material-weighted stretch of the eval and overlaps with EvalMatScale (planted s=20 fitted as k=120 nearly as well)" are
adopted in the reading below.
### Inputs
- `logs/inputs.sha256` now also lists the 6 gate PGNs (sha256 taken 2026-11-02 10:25 PC clock). Finding: the PGNs are not
  all the R13 state: `uhoSF26bit1_razor_e417_vs_AL1lp.pgn` grew from 1,093 games (R13 read it while that gate was still
  running) to 2,998; the other 5 files give byte-identical extracted rows (447,280 positions, same .tsv / .fens content),
  so their hashes also describe R13's input. R13 did not hash the razor PGN at its 1,093-game state; R13's own outputs
  (al1gates.fens / .tsv / .evals, first 3 lines of inputs.sha256) pin the data every fit below uses.
- A fresh R14 extraction of the grown PGNs (13,795 games, 574,366 positions, `logs/r14_extraction.sha256`) is available;
  fits on it are NOT run in R14 (run_p7_r14b.sh is ready; the bound question uses R13's exact data).
### Regression: the R14 fit_e3.py at the default bounds (50, 150, 60) reproduces R13's fit_e3.json exactly
(every set, loss, slope, CI equal; the json only gains `bounds_s_k_d`, `at_upper_bound`, `slope_at_bound`); both fitted
values are flagged K-AT-BOUND / D-AT-BOUND (logs/fit_e3_default_r14.json).
### Refit once with wider bounds (50, 400, 100) on R13's data (logs/fit_e3_wide.json; D <= 100: at 100 the damping zeroes the eval at clock 100)
| set | held-out log-loss | vs OFF, 95 % CI (game bootstrap 2000) | on a bound? |
|---|---|---|---|
| OFF | 0.569080 | - | - |
| EvalRule50Damp only: d = **81** (was 60 = old max) | 0.566624 | -0.002456 [-0.003777, -0.001333] | no |
| EvalOptimism only (static approximation, WEAK): k = **228** (was 150) | 0.567205 | -0.001875 [-0.002798, -0.001055] | no |
| EvalMatScale only | 0 = OFF | 0 | - |
| all three: (0, 185, 72) (was (0, 150, 60)) | 0.565484 | -0.003596 [-0.005247, -0.002191] | no |
Past the old bound vs the bound value itself (paired game bootstrap, compare_sets.py, logs/compare_wide_vs_bound.json):
| A vs B | held-out loss A - B, 95 % CI | reading |
|---|---|---|
| Rule50Damp 81 vs 60 | -0.000318 [-0.000632, -0.000039] | 81 better, barely separated |
| Optimism 228 vs 150 | -0.000166 [-0.000450, +0.000085] | not separated |
| all three (0,185,72) vs (0,150,60) | -0.000156 [-0.000397, +0.000052] | not separated |
| Rule50Damp 81 vs the hand value 30 | -0.001191 [-0.001996, -0.000498] | clearly better |
Reading (calibration of a static eval, not playing strength; only a gate decides): the Rule50Damp optimum lies past the E3
option bound (~81 vs max 60) and is a little better calibrated than 60; Optimism's optimum also lies past 150, but not
separated from 150 - and it is weak evidence anyway (static stand-in for the root score, overlap with MatScale). MatScale
stays 0.
### Candidate lines (crew's E3 exe; UNPROVEN; each line on its own, never bundled)
1. `setoption name EvalRule50Damp value 60` - the best value the E3 option range allows (fit-only optimum 81 is outside it).
2. Optional, weak evidence, on its own (NEVER together with Rule50Damp): `setoption name EvalOptimism value 150`.
3. No MatScale line; the "all three" rows are fit-only, not a gate line.
Owner item: gating Rule50Damp ~80 needs an E3 build whose EvalRule50Damp max is >= 81 (crew's E3 source; default 0, so OFF
stays the lock) - worth it only after the crew's E3 hand gate uhoE3c (Rule50Damp 30, running since 05:18 PC clock) says the
direction helps at all.

### Review milestone R14-P7-1 (structured self-review, NOT independent - no sub-agents in R14)
- Reviewed: fit_e3.py / extract_positions.py / compare_sets.py diffs, the regression json compare, the wide fit and the
  bootstrap; candidate = fit values only (no exe built).
- Findings: (1) the PGN growth (found by the re-extraction, cause pinned to one file) - documented above, the fits stay on
  R13's hashed outputs; (2) a fitted value at the end of its search range says nothing about the optimum - the bound flags
  (CR 129d440e) now mark it, and the wide refit answered it; (3) none open.
