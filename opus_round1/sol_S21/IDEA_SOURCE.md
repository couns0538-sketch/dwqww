# IDEA_SOURCE — S21 int16 range study

- **Spec:** Sol's S21 (`17aa0cae:…/forge_sol_all_jobs_inventory_20261026.json`, id S21; NOT_STARTED): per-net int16
  range report over 200k positions plus a clipped-export tool that states the float-parity loss; study only, no
  int16 H256 engine path (rule 8; crew rework 10:30: research only, no engine patch).
- **Inputs (lock archive, read-only):** the 13 nets of `5_nnue/nets/history_all_CR_passed/NETS_MANIFEST_13_forge_nets_20261025.md`,
  CR's `CR_HOLD_sol_nnueint16_b425207a_overflow_table.txt` (weight bounds reproduced exactly), the data32 sample
  (200k positions), `5_nnue/tools/nnue_check.cpp` (engine harness) and `eval_inc.py` / `check_export.py` (the .inc
  format and scale). Feature mapping and forward pass from `train_resid_v3b.py` (`features()`, `NNUE.forward`).
- **Method:** standard quantization analysis (range histograms, saturation/wrap simulation, uniform rescaling of a
  layer to a narrower integer type and measuring the output error). No code was copied from any third-party project.
