# S30 [Sol leftover] Epoch and data-size learning-curve study — DONE (real-data conclusions UNVERIFIED until gated)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 14. Branch `opus-sol-S30` = `d4f4312` + `0d99f02` cherry-picked
(`b3db70b6`) + this commit. Analysis job, no engine change, `[skip ci]`. Sol never started S30. A light sub-agent
located the inputs earlier; it was wound down before writing any code. This session wrote the tools, ran them and
wrote the study.

**The study:** `forge_sol_S30_epoch_study_20261027.md` (every number cites a file and line).

## Acceptance (Sol's pass line)
| line | result | evidence |
|---|---|---|
| every claim cites a file and line | **PASS** | the study cites RUNS `<log>:<line>` for every FINAL loss (from `final_table.csv`'s `where` column), `GATE_RESULTS_SUMMARY_20261025_1215.md` and `LATEST_GATE_FACTS_20261026.md` lines for every gate, and `NNUE_NEXT_WEEK_PLAN.md` lines for every quoted reading |
| any holdout gap smaller than the seed spread is labelled noise | **PASS** | pooled seed sd b0.6 7.1e-6 (13 groups); e24 vs e48 gap 1.6e-5 labelled noise-level; predicted e64 gain about 6e-6 below one sd |
| reruns reproduce exactly | **PASS** | log parse and fit: byte-identical reruns (`logs/step1_log_curves.log`, `logs/step2_fit.log`); replicas r1 = r2 byte-identical (artifacts and losses, `logs/step3_replicas.log`) |
| says plainly that loss alone has not predicted Elo for us | **PASS** | study §5 (and the summary at its top) |
| no GPU | **PASS** | CPU only (replicas: CPU, one Torch thread) |
| real-data conclusions marked UNVERIFIED | **PASS** | study header and §6 |
| Part 2: tiny CPU replicas, 4 data sizes × 3 epoch counts, fixed seeds, fit | **DONE (pipeline only)** | `opus_nnue_smoke_s30_replica.py`: H64, 4k/8k/16k/32k positions × 2/4/8 epochs, seed 25, two passes, byte-identical. On the synthetic data32 sample the net only fits noise (loss rises with steps), so no real-data fit is drawn from it |
| tests, planted bugs | **PASS** | 3/3 tests on synthetic log fixtures (`logs/step4_tests.log`); 6/6 mutants caught (`logs/step5_mutation_check.log`) |

## Main findings (details and citations in the study)
1. **"e48 beat e32" is not shown by the games.**
   - G104 (e48 f006) stopped early at 698 games (+29.44); its confirm G104c gave +7.18 ±8.49 (cap).
   - The e32 cap points are +8 to +11 (unpooled effect sizes only).
   - AL1 is the e32 recipe.
   - Four e48 nets gated against AL1 did not lock.
2. **Epochs at fixed data move loss by noise-level amounts.**
   - e24 → e48: b0.6 −1.6e-5, and teacher loss worse.
   - The fitted L(64) improves on e48 by about 6e-6.
3. **Data size is the only lever above noise:** −1.68e-4 b0.6 per doubling of training positions at the fixed e48
   recipe (CI −1.84e-4 … −1.41e-4; 23 runs, 137M-222M positions).
4. **Loss has not predicted Elo for us:**
   - teacher loss runs against games across blend-ends;
   - b0.6 gaps below 0.5% do not predict a gate;
   - four e48 nets with a b0.6 4-8 seed-sds better than AL1's net failed to lock.
5. **Recommendation (UNVERIFIED):** if a gate is spent, spend it on more data with the e48 recipe (one factor
   changed). e64 is not supported by loss. A longer low-LR tail has no isolating run yet.

## Safety (PC rules)
- The run logs were read only.
- The replicas used a byte-identical trainer copy named `opus_nnue_smoke_s30_v3b.py` and wrote only to
  `F:\opus_scratch\sol_S30\replicas\r1|r2`.
- Runs were one Torch thread at BelowNormal, with a 6 GiB available-RAM check before each run and a supervisor-log
  check during each run.
- The supervisor log shows no new "adopted running job" line: its 7 such lines are the earlier, resolved C4/C5
  incident.
- Machine exclusive: no.

## Files
- `forge_sol_S30_epoch_study_20261027.md` (the study), `REPORT.md`, `IDEA_SOURCE.md`;
- `forge_sol_S30_log_curves.py`, `forge_sol_S30_fit.py`, `opus_nnue_smoke_s30_replica.py`;
- `test_forge_sol_S30.py`, `mutation_check_s30.py`;
- `logs/step1_log_curves.log`, `step2_fit.log`, `step3_replicas.log`, `step4_tests.log`, `step5_mutation_check.log`;
- `logs/s30_outputs.tar.gz` (`final_table.csv`, `epoch_curves.csv`, `seed_spread.csv`, `summary.json`, `fit.json`, the
  replica JSONs and stdout);
- `FILES`, `SHA256SUMS`.

## UNVERIFIED / left
- Every real-data recommendation until a gate tests it.
- The low-LR-tail question: no run isolates it.
- A replica study on real data: it would need a real sample, not data32.
