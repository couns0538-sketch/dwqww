#!/usr/bin/env bash
# FB2-J7 follow-up: baseline vs second-layer prototype at 60 minutes each (one thread), same protocol as run_j7.sh.
set -uo pipefail
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=/f/opus_scratch/fable/tmp TEMP=/f/opus_scratch/fable/tmp
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
HO=/f/opus_scratch/fable/data/holdout/fb2_holdout_200k
J7=/f/opus_scratch/fable/fb2/j7
cd /f/opus_scratch/worktrees/fable_fb2_j7
: > "$J7/runs60_summary.txt"
run() { # name extra-args...
  local name=$1; shift
  nice -n 19 "$PY" -I -B tools/nnue/fable_nnue_train.py train \
    --pos-glob "F:/opus_scratch/fable/data/train/fb2_train_*.pos" --hce-dir F:/opus_scratch/fable/data/train \
    --output-buckets 8 --mirror --steps 93000 --batch 8192 --lr 1e-3 --lr-schedule cosine --lr-final 5e-5 --warmup-steps 500 \
    --blend-schedule linear --blend-start 0.9 --blend-end 0.6 --chunk-rows 250000 --chunks 8 --refresh-every 25 --shard-weighting rows \
    --exact-pos "$HO.pos" --exact-hce "$HO.hce" --ckpt-every-minutes 15 --ckpt-at-pause --max-minutes 60 --threads 1 --seed 1 --float-exact \
    "$@" --out "$J7/run_$name" > "$J7/run_$name.log" 2>&1
  echo "$name exit $?" >> "$J7/runs60_summary.txt"
}
run l2_60   --hidden 512 --king-buckets 8 --l2 16
run base_60 --hidden 512 --king-buckets 8
echo "j7 60-minute runs done" >> "$J7/runs60_summary.txt"
