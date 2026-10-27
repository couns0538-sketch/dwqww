#!/usr/bin/env bash
# C5 local CPU smoke training (scratch copy of tools/nnue/train_resid_v3b.py as opus_nnue_smoke.py), 1 torch thread
# (run1t.py), nice 19, CPU torch venv (read-only use). Every output stays under F:/opus_scratch/c5.
# usage: run_smoke.sh <name> [extra trainer args...]
set -u
S=/f/opus_scratch/c5
V=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
D=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039/5_nnue/sample_data/data32_sample/data32_sample_50k
name=$1; shift
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$S" || exit 1
{
  echo "# C5 CPU smoke training '$name': scratch copy F:/opus_scratch/c5/opus_nnue_smoke.py (= tools/nnue/train_resid_v3b.py, md5 $(md5sum opus_nnue_smoke.py | cut -c1-32)), torch 2.4.1+cpu, 1 thread (run1t.py), nice 19; data 5_nnue/sample_data/data32_sample/data32_sample_50k (train t00000-t03000 = 200k, holdout h000 = 50k, read only)"
  echo "\$ python run1t.py opus_nnue_smoke.py --train <sample>/t0*.pos --holdout <sample>/h000.pos --hce-dir <sample> --device cpu --residual --init-check --shape 256 --epochs 3 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 --steps-per-epoch 200 --val-positions 16384 --log-every 30 $* --run-dir F:/opus_scratch/c5/smoke_$name"
  nice -n 19 "$V" run1t.py opus_nnue_smoke.py --train "$D/t0*.pos" --holdout "$D/h000.pos" --hce-dir "$D" --device cpu --residual \
    --init-check --shape 256 --epochs 3 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 \
    --steps-per-epoch 200 --val-positions 16384 --log-every 30 "$@" --run-dir "F:/opus_scratch/c5/smoke_$name" 2>&1
  echo "trainer exit status $?"
  echo "-- outputs (sha256)"
  (cd "smoke_$name" && sha256sum epoch003-*)
} > "$S/smoke_$name.log" 2>&1
tail -4 "$S/smoke_$name.log"
