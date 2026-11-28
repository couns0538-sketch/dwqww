#!/usr/bin/env bash
# Server-Day v3 Double-Buffered Streaming GPU Trainer Wrapper (Linux / H100 / 4090 / 7900 XT)
# Hardened per Wave 7 Stream B audit:
#   - Defaults to primary Server-Day architecture: --hidden 1024 --king-buckets 16 (-0.6% NPS vs kb8!)
#   - Double-defense: ALWAYS passes --skip-fqs-noisy (bit0=0) and keeps bit1=0 (in_check dropped)
#   - Injects all 3 frozen disjoint anchors (dead_draws_20k_s5disjoint, won_endings_syzygy_20k, opening_ply012_anchors)
#   - Atomic resume_ckpt.pt is saved automatically every superbatch by train_v3p_stream.py
#   - Optional OB_REWEIGHT (default "none" — S2Q_G4b rejected at 250k: -5.21 [-24.09, +13.64]) & LOSS_POW (default "2.0")
set -euo pipefail

unset HIP_VISIBLE_DEVICES CUDA_VISIBLE_DEVICES ROCR_VISIBLE_DEVICES || true
export TORCHDYNAMO_DISABLE=1
export PYTHONDONTWRITEBYTECODE=1

FORGE_LAB_ROOT="${FORGE_LAB_ROOT:-/workspace/nnue-lab}"
SHARDS_DIR="${1:-${FORGE_LAB_ROOT}/data/clean_2b_quiet_avg}"
OUT_DIR="${2:-${FORGE_LAB_ROOT}/runs/serverday_1024p_kb16}"
HIDDEN="${HIDDEN:-1024}"
KING_BUCKETS="${KING_BUCKETS:-16}"
EPOCHS="${EPOCHS:-20}"
LR="${LR:-0.0008}"
LR_CYCLES="${LR_CYCLES:-2}"
BATCH_SIZE="${BATCH_SIZE:-16384}"
MIX="${MIX:-0.85}"
LOSS_POW="${LOSS_POW:-2.0}"
OB_REWEIGHT="${OB_REWEIGHT:-none}"
ANCHOR_REPEAT="${ANCHOR_REPEAT:-25}"
SEED="${SEED:-1}"

ANCHORS_DIR="${FORGE_LAB_ROOT}/neon/forge_fixes/anchors"
mkdir -p "${OUT_DIR}"

EXTRA_ARGS=()
if [[ "${OB_REWEIGHT}" != "none" ]]; then
  EXTRA_ARGS+=(--ob-reweight "${OB_REWEIGHT}")
fi

python3 -B "${FORGE_LAB_ROOT}/neon/forge_fixes/train_v3p_stream.py" \
  --fqs-shards "${SHARDS_DIR}" \
  --anchor-shards \
    "${ANCHORS_DIR}/dead_draws_20k_s5disjoint.fqs.z" \
    "${ANCHORS_DIR}/won_endings_syzygy_20k.fqs.z" \
    "${ANCHORS_DIR}/opening_ply012_anchors.fqs.z" \
  --anchor-repeat-per-sb "${ANCHOR_REPEAT}" \
  --out-dir "${OUT_DIR}" \
  --hidden "${HIDDEN}" \
  --king-buckets "${KING_BUCKETS}" \
  --epochs "${EPOCHS}" \
  --lr "${LR}" \
  --lr-cycles "${LR_CYCLES}" \
  --batch-size "${BATCH_SIZE}" \
  --mix "${MIX}" \
  --loss-pow "${LOSS_POW}" \
  --skip-fqs-noisy \
  --use-shard-weights \
  --save-cycles \
  --seed "${SEED}" \
  "${EXTRA_ARGS[@]}"
