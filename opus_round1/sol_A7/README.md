# Astra A7: long-training recipe design for the H256 residual net

The deliverable is `forge_astra_A7_long_recipe_20261027.md`. Its three queue lines are in
`forge_astra_A7_queue_lines_20261027.txt` (PROPOSED, UNPROVEN, not queued).

## Tools
- `opus_a7_curve_stats.py`: statistics from the PC's finished runs. It needs the S30 parser's CSVs and the run logs,
  both read-only. It computes the seed sd, the data/epoch/lr fits with bootstrap CIs, the plateau epochs, and the
  throughput and memory from the `Finished:` / `MEM` lines. It writes `a7_stats.json` and `a7_tables.md`.
- `opus_a7_dryparse.py`: dry-parses queue lines with the unchanged v3b argument parser. That parser is the
  `ast`-extracted `ArgumentParser` and `add_argument` statements of a byte-identical renamed copy (md5 checked), so no
  trainer code runs.
  - Positive control: a finished run's argv must reproduce the settings JSON the trainer wrote.
  - Negative controls: lines named `NEGATIVE_*` must be rejected.
  - It also prints steps, positions and GPU hours per line.
- `test_opus_a7.py` (9 tests) and `mutation_check_a7.py` (6 planted bugs, all must be caught).

## Reproduce (paths of this run)
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
# 1. S30's parser (branch opus-sol-S30, unchanged) over the run logs
$PY -I -B forge_sol_S30_log_curves.py --runs 'F:\forge_nnue_train\runs' --out <new dir>/curves
# 2. statistics
$PY -I -B opus_a7_curve_stats.py --curves <new dir>/curves --runs 'F:\forge_nnue_train\runs' --out <new dir>/stats
# 3. dry parse (the trainer copy must be named opus_nnue_smoke_*.py, never train_resid*)
cp <LA>/5_nnue/trainers/train_resid_v3b.py <scratch>/opus_nnue_smoke_a7_v3b.py
$PY -I -B opus_a7_dryparse.py --trainer-copy <scratch>/opus_nnue_smoke_a7_v3b.py --expect-md5 b6758004d19837c8d34d401ee7af5fd5 \
  --settings 'F:\forge_nnue_train\runs\resid_h256_e48_f070_bs16k_lr10e4_b06_s89_fb8k\settings_1793108660.txt' \
  --ref-queue-args "<f070's queue.txt args>" --lines forge_astra_A7_queue_lines_20261027.txt \
  --rate-measured 1344201 --max-train-available 241913894 --out <new dir>/dryparse
# 4. tests and planted bugs
$PY -I -B test_opus_a7.py -v
$PY -I -B mutation_check_a7.py --work <new dir>/mutants
```
Every tool refuses an existing output directory. Run everything at Idle (`nice -n 19`) with one thread.
