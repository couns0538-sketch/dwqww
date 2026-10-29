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

Results: see the report section J7 (filled in when the runs have finished).
