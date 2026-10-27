# IDEA_SOURCE — S30 epoch and data-size learning-curve study

- **Spec:** Sol's S30 (`17aa0cae:…/forge_sol_all_jobs_inventory_20261026.json`, id S30; NOT_STARTED) and the rule note
  12:15 on capped gates.
- **Inputs (read-only):** the PC's NNUE run logs (`F:\forge_nnue_train\runs\*.log`, `*.cmd.txt`); the lock archive's
  `7_history/gate_results/GATE_RESULTS_SUMMARY_20261025_1215.md`, `7_history/LATEST_GATE_FACTS_20261026.md`,
  `5_nnue/docs/NNUE_NEXT_WEEK_PLAN.md`; the data32 sample and the v3b trainer (renamed copy) for the replicas.
- **Methods:** log parsing with file:line provenance; seed spread as the pooled within-recipe sd; least-squares
  power-law and log-linear learning-curve fits with bootstrap / leave-one-out ranges (standard scaling-law practice,
  e.g. Kaplan et al. 2020 "Scaling Laws for Neural Language Models" for the functional forms). No code was copied.
