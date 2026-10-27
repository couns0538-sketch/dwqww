# IDEA_SOURCE — S19 score-to-WDL scale fit per phase

- **Spec:** Sol's S19 (`17aa0cae:…/forge_sol_all_jobs_inventory_20261026.json`, id S19; Sol never started it):
  fit a per-phase sigmoid scale with CI to map STM score to WDL; held-out log-loss at least as good as the current
  constant; crew rework 10:30: the f006 recipe's settings are the reference constant.
- **Model and reference:** the v3b trainer's teacher `sigmoid(clamp(score * k / 400, ±40))` and `K_DEFAULT = 2.25`
  (`train_resid_v3b.py` `targets()`, lock archive `5_nnue/trainers/`); data layout from
  `5_nnue/datagen_and_format/record_format/RECORD_FORMAT_v3b_pos_hce_20261025.md`; the text game-split rule from
  `holdout_reference/build_forge_holdout_gamesplit_reference.py`; phase weights from `include/forge/eval.hpp`.
- **Methods:** logistic regression without intercept fitted by Newton's method; percentile bootstrap intervals
  (cluster bootstrap by game where games are known); a "keep the constant unless the CI excludes it" selection
  rule. Generic statistics; the idea of fitting the eval-to-WDL scale per material phase is common in engine
  tuning (e.g. Texel-tuning scale fits, CPW "Texel's Tuning Method"). No code was copied from any project.
