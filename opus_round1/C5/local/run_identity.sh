#!/usr/bin/env bash
# C5 trainer without --output-buckets: outputs must be byte-identical to the original v3b (default mode; md5s
# recorded in opus_round1/C4/logs/trainer_default_identity.log) and to the C4 trainer (--king-buckets 4 mode; C4
# smoke run, opus_round1/C4/logs/smoke_train_kb4.log). Scratch copy opus_nnue_smoke.py, 1 torch thread, nice 19;
# every output under F:/opus_scratch/c5.
set -u
S=/f/opus_scratch/c5
V=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
D=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039/5_nnue/sample_data/data32_sample/data32_sample_50k
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$S" || exit 1
COMMON=(--train "$D/t0*.pos" --holdout "$D/h000.pos" --hce-dir "$D" --device cpu --residual --init-check --shape 256)
{
  echo "# C5 trainer (scratch copy opus_nnue_smoke.py = tools/nnue/train_resid_v3b.py of opus-C5, md5 $(md5sum opus_nnue_smoke.py | cut -c1-32)) without --output-buckets"
  echo "## 1. default mode, the arguments of opus_round1/C4/logs/trainer_default_identity.log (--epochs 2 --lr 7.07e-4 --blend-end 0.6 --seed 99 --batch-size 1024 --warmup-steps 5 --steps-per-epoch 15 --val-positions 4096)"
  nice -n 19 "$V" run1t.py opus_nnue_smoke.py "${COMMON[@]}" --epochs 2 --lr 7.07e-4 --blend-end 0.6 --seed 99 --batch-size 1024 \
    --warmup-steps 5 --steps-per-epoch 15 --val-positions 4096 --run-dir F:/opus_scratch/c5/identity_default > identity_default.out 2>&1
  echo "trainer exit status $?"
  (cd identity_default && md5sum epoch00*)
  echo "## 2. --king-buckets 4, the arguments of the C4 smoke run (opus_round1/C4/logs/smoke_train_kb4.log: --epochs 3 --lr 2e-3 --seed 20261026 --steps-per-epoch 200 ...)"
  nice -n 19 "$V" run1t.py opus_nnue_smoke.py "${COMMON[@]}" --epochs 3 --lr 2e-3 --blend-end 0.6 --seed 20261026 --batch-size 1024 \
    --warmup-steps 30 --steps-per-epoch 200 --val-positions 16384 --king-buckets 4 --log-every 30 --run-dir F:/opus_scratch/c5/identity_kb4 > identity_kb4.out 2>&1
  echo "trainer exit status $?"
  (cd identity_kb4 && sha256sum epoch003-*)
} > identity.log 2>&1
cat identity.log
