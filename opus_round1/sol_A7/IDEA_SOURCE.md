# A7 idea sources

- **Spec:** `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 37 / Sol's inventory `astra_jobs` id A7 (spec line 575).
  - Inputs named there: `files/18_training_logs/` and `files/07_nnue_context/`.
  - Their copies in the lock archive: `5_nnue/docs/{AUTO_RESULTS.md, NETS_snapshot_20261025_1030.md,
    NNUE_NEXT_WEEK_PLAN.md}`, `5_nnue/trainers/train_resid_v3b.py` (arguments read only) and
    `7_history/gate_results/GATE_RESULTS_SUMMARY_20261025_1215.md`.
  - Newer facts come from `7_history/LATEST_GATE_FACTS_20261026.md` and the PC's run logs
    (`F:\forge_nnue_train\runs`, read-only).
- **Earlier Opus studies reused:**
  - S30 (`opus-sol-S30`): log parser, seed spread, the finding that loss did not predict Elo.
  - S44 (`opus-sol-S44`): Elo per 1e-4 of b0.6, and e64/e96 versus more-data projections.
  - S31 (`opus-sol-S31`): checkpoint averaging, as an alternative to longer runs; not used in the lines.
- **General practice (concepts only):**
  - Cosine decay with warmup and a floor, which is the trainer's existing schedule.
  - Changing one factor per experiment, with a same-seed control ("common random numbers").
  - Judging a schedule by the final, annealed checkpoint rather than mid-run ones: a cosine run's mid-run checkpoints
    are not shorter runs.
  - No code was copied.
