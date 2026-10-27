# S-A1 more-data retrain recipe (G-A1)

- `forge_sol_SA1_more_data_recipe_20261027.md`: the recipe. It covers what exists (S16/S17/S32/S40/A7/S44), measured data
  growth, the memory wall at 0.5B+, the steps, the gate and the queue lines.
- `forge_sol_SA1_queue_lines_20261027.txt`: 4 PROPOSED queue lines, plus 2 negative controls and 1 abbreviation-hazard
  line for the dry parse.
- `opus_a7_dryparse.py`: A7's dry-parse tool (byte-identical copy, sha256 `1c400cfc…`). It parses queue lines with the
  unchanged v3b parser extracted from a renamed trainer copy; no trainer code runs. Tests and planted bugs are on
  branch `opus-sol-A7`.

```
python -I -B opus_a7_dryparse.py --trainer-copy <scratch>/opus_nnue_smoke_a7_v3b.py --expect-md5 b6758004d19837c8d34d401ee7af5fd5 \
  --settings 'F:\forge_nnue_train\runs\resid_h256_e48_f070_bs16k_lr10e4_b06_s89_fb8k\settings_1793108660.txt' \
  --ref-queue-args "<f070's queue.txt args>" --lines forge_sol_SA1_queue_lines_20261027.txt \
  --rate-measured 1344201 --max-train-available 1000000000 --out <new dir>
```
