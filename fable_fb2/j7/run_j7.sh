#!/usr/bin/env bash
# FB2-J7 prototype runs: 30 minutes each on one thread, same data/seed/schedules, float holdout metric.
set -uo pipefail
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=/f/opus_scratch/fable/tmp TEMP=/f/opus_scratch/fable/tmp
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
HO=/f/opus_scratch/fable/data/holdout/fb2_holdout_200k
J7=/f/opus_scratch/fable/fb2/j7
MIN=${J7_MINUTES:-30}
cd /f/opus_scratch/worktrees/fable_fb2_j7
: > "$J7/runs_summary.txt"
run() { # name extra-args...
  local name=$1; shift
  nice -n 19 "$PY" -I -B tools/nnue/fable_nnue_train.py train \
    --pos-glob "F:/opus_scratch/fable/data/train/fb2_train_*.pos" --hce-dir F:/opus_scratch/fable/data/train \
    --output-buckets 8 --mirror --steps 93000 --batch 8192 --lr 1e-3 --lr-schedule cosine --lr-final 5e-5 --warmup-steps 500 \
    --blend-schedule linear --blend-start 0.9 --blend-end 0.6 --chunk-rows 250000 --chunks 8 --refresh-every 25 --shard-weighting rows \
    --exact-pos "$HO.pos" --exact-hce "$HO.hce" --ckpt-every-minutes 10 --ckpt-at-pause --max-minutes "$MIN" --threads 1 --seed 1 --float-exact \
    "$@" --out "$J7/run_$name" > "$J7/run_$name.log" 2>&1
  echo "$name exit $?" >> "$J7/runs_summary.txt"
}
# base, h1024 and kb16 ran on 2026-10-28 19:05-19:37 (results in fable_fb2/j7); the remaining prototypes:
run l2    --hidden 512  --king-buckets 8 --l2 16
run pair  --hidden 512  --king-buckets 8 --pairwise
echo "j7 runs done" >> "$J7/runs_summary.txt"
