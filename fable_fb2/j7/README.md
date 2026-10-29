# FB2-J7: NNUE v4 ideas prototyped in the trainer (branch `fable-fb2-j7`)

Trainer: `tools/nnue/fable_nnue_train.py` (the J1 trainer plus `--l2 N`, `--pairwise`, `--float-exact`). Prototype
checkpoints are `.pt` models (no v3 file), scored on the 200k FB2 holdout with the float forward (`float_score`);
the baseline run uses `--float-exact` so all runs share the metric.

Protocol (one thread each, `nice -n 19`, same data/seed/batch/LR/WDL schedule as J1, 30 minutes per run):
```
COMMON="train --pos-glob F:/opus_scratch/fable/data/train/fb2_train_*.pos --hce-dir F:/opus_scratch/fable/data/train
  --king-buckets 8 --output-buckets 8 --mirror --steps 93000 --batch 8192 --lr 1e-3 --lr-schedule cosine --lr-final 5e-5
  --warmup-steps 500 --blend-schedule linear --blend-start 0.9 --blend-end 0.6 --chunk-rows 250000 --chunks 8 --refresh-every 25
  --exact-pos <holdout.pos> --exact-hce <holdout.hce> --ckpt-every-minutes 10 --ckpt-at-pause --max-minutes 30 --threads 1 --seed 1 --float-exact"
baseline : $COMMON --hidden 512  --out .../j7_base
P1 H1024 : $COMMON --hidden 1024 --out .../j7_h1024
P2 KB16  : $COMMON --hidden 512 --king-buckets 16 --out .../j7_kb16
P3 L2    : $COMMON --hidden 512 --l2 16 --out .../j7_l2
P4 pair  : $COMMON --hidden 512 --pairwise --out .../j7_pair
```
Compare `status.json` of each run: float b0.6 at the 10/20/30-minute checkpoints and positions seen (the wider nets
see fewer positions per minute, so the table reports both "at equal time" and "at equal positions" where available).

Results (float holdout b0.6 on the 200k FB2 holdout; positions seen in brackets; one seed; `logs/run_*_log.txt`):

| run | 10 min | 20 min | 30 min |
|---|---|---|---|
| baseline H512 / 8 king buckets | 0.017107 (14.0M) | 0.016408 (27.5M) | 0.016088 (41.3M) |
| H1024 / 8 | 0.017935 (7.6M) | 0.016738 (14.9M) | 0.016401 (22.1M) |
| H512 / 16 king buckets | 0.017224 (13.6M) | 0.016429 (27.0M) | 0.016242 (40.1M) |
| H512 / 8 + second layer 16 | 0.016835 (13.8M) | 0.016086 (26.9M) | **0.015759** (40.5M) |
| H512 / 8 + pairwise term | 0.017083 (13.9M) | 0.016358 (27.3M) | 0.016138 (40.5M) |

The second layer is the only prototype clearly ahead of the baseline at equal positions and equal time; it needs
a v4 engine format (int8/int16 second layer with per-bucket output weights) before it can be gated.
