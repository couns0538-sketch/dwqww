# S19 score-to-WDL scale fit per phase

`forge_sol_S19_wdl_scale_fit.py` fits the scale `k` of the trainer's teacher, `p = sigmoid(clamp(score * k / 400, ±40))`
(side-to-move centipawns → the side to move's result), per game phase, and compares held-out log-loss with the
constant `k = 2.25` that the v3b trainer and the f006 recipe use (`K_DEFAULT`, `--sigmoid-k` default).

```sh
# .pos inputs (v3b record format): fit files and held-out files
python -I -B forge_sol_S19_wdl_scale_fit.py --fit-pos A.pos B.pos --holdout-pos H.pos --out result.json [--stride N]
# text inputs ("FEN | stm_cp | white_result"): split into fit/held-out by game
python -I -B forge_sol_S19_wdl_scale_fit.py --text sample.txt --holdout-frac 0.3 --out result.json
```
Needs numpy (the NNUE venv has numpy 1.26.4). Writes `result.json` and `result.md` (both must be new files);
reads its inputs through read-only memory maps.

- **Phase:** Forge's HCE material phase (`eval.hpp`: N 1, B 1, R 2, Q 4, pawns and kings 0; both sides; clamped at
  24). Default buckets `0-3, 4-7, 8-11, 12-15, 16-19, 20-24` (`--edges`).
- **Fit:** Newton's method on the convex log-loss in `k` (cross-entropy with the 0 / 0.5 / 1 target), per bucket.
- **Interval:** percentile bootstrap, 95%. The unit is the game when games are known (text inputs), otherwise the
  row. `.pos` files have no game ids, so a row bootstrap understates the uncertainty.
- **Delivered table:** a bucket uses its fitted `k` only when it has at least `--min-rows` (200) fit rows AND its
  CI excludes 2.25; otherwise it keeps 2.25.
- **Held-out log-loss:** reported for the constant 2.25, one global fitted `k`, every bucket fitted, and the
  delivered table.
- **Text inputs:** scores are clipped to ±3000 cp (as the text→.pos converter does). Games are rebuilt from line
  order: a new game starts when the fullmove number falls, the piece count rises or the result changes (the rule
  of `build_forge_holdout_gamesplit_reference.py`). Held-out games: `sha1("<file>#<game>" + seed) % 10000 < frac * 10000`.
- **Deterministic:** fixed seeds and iterations, sorted JSON (`logs/step2b_determinism.log`).

Tests: `python -I -B test_forge_sol_S19_wdl_scale_fit.py` (12 tests; set `S19_SAMPLE_DIR` to the lock archive's
`5_nnue/sample_data` for the real-sample cross-check). Planted bugs: `python -I -B mutation_check_s19.py <new dir>`.
