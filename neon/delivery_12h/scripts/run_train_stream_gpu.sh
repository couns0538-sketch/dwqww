#!/usr/bin/env bash
set -euo pipefail

# Portable lab root for Linux GPU training (set KEEP_VISIBLE_DEVICES=1 to preserve explicit GPU masks)
export FORGE_LAB_ROOT="${FORGE_LAB_ROOT:-/workspace/nnue-lab}"
export TORCHDYNAMO_DISABLE="${TORCHDYNAMO_DISABLE:-1}"
export PYTHONDONTWRITEBYTECODE=1
export FORGE_MIN_FREE_RAM_GB="${FORGE_MIN_FREE_RAM_GB:-1.5}"

if [[ "${KEEP_VISIBLE_DEVICES:-0}" != "1" ]]; then
  unset HIP_VISIBLE_DEVICES CUDA_VISIBLE_DEVICES ROCR_VISIBLE_DEVICES
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
FQS_SHARDS="${FQS_SHARDS:-${FORGE_LAB_ROOT}/data/clean_2b_avg}"
OUT_DIR="${OUT_DIR:-${FORGE_LAB_ROOT}/runs/serverday_2b_1024p}"
ANCHOR_DIR="${ANCHOR_DIR:-${FORGE_LAB_ROOT}/neon/forge_fixes/anchors}"

DISTILL_NET="${DISTILL_NET:-${FORGE_LAB_ROOT}/neon/forge_fixes/gpu_runs/G2_v3p_1024_pairwise_psqt/cand.pt}"
DISTILL_WEIGHT="${DISTILL_WEIGHT:-0.2}"
SHARDS_PER_SB="${SHARDS_PER_SB:-400}"
ANCHOR_REPEAT="${ANCHOR_REPEAT:-25}"
HIDDEN="${HIDDEN:-1024}"
EPOCHS="${EPOCHS:-20}"
BATCH_SIZE="${BATCH_SIZE:-8192}"
LR="${LR:-0.0005}"
MIN_LR_FRAC="${MIN_LR_FRAC:-0.05}"
WARMUP_STEPS="${WARMUP_STEPS:-500}"
LR_CYCLES="${LR_CYCLES:-auto}"
W1_DECAY="${W1_DECAY:-0.3}"
OB_SMOOTH="${OB_SMOOTH:-2e-6}"
MIX="${MIX:-0.75}"
LOSS_POW="${LOSS_POW:-2.0}"
SEED="${SEED:-1}"
DRY_RUN="${DRY_RUN:-0}"

EXTRA_ARGS=()
for arg in "$@"; do
  if [[ "${arg}" == "--dry-run" ]]; then
    DRY_RUN=1
  else
    EXTRA_ARGS+=("${arg}")
  fi
done

SCRIPT_PATH="${FORGE_LAB_ROOT}/neon/forge_fixes/train_v3p_stream.py"

CMD=(
  "${PYTHON_BIN}" -B "${SCRIPT_PATH}"
  --fqs-shards "${FQS_SHARDS}"
  --anchor-shards
    "${ANCHOR_DIR}/dead_draws_20k_s5disjoint.fqs.z"
    "${ANCHOR_DIR}/won_endings_syzygy_20k.fqs.z"
    "${ANCHOR_DIR}/opening_ply012_anchors.fqs.z"
  --anchor-repeat-per-sb "${ANCHOR_REPEAT}"
  --shards-per-superbatch "${SHARDS_PER_SB}"
  --use-shard-weights
  --hidden "${HIDDEN}"
  --epochs "${EPOCHS}"
  --batch-size "${BATCH_SIZE}"
  --lr "${LR}"
  --min-lr-frac "${MIN_LR_FRAC}"
  --warmup-steps "${WARMUP_STEPS}"
  --lr-cycles "${LR_CYCLES}"
  --w1-decay "${W1_DECAY}"
  --ob-smooth "${OB_SMOOTH}"
  --mix "${MIX}"
  --loss-pow "${LOSS_POW}"
  --distill-net "${DISTILL_NET}"
  --distill-weight "${DISTILL_WEIGHT}"
  --save-cycles
  --seed "${SEED}"
  --mem-need-gb 0
  --resume
  --out-dir "${OUT_DIR}"
)

if (( ${#EXTRA_ARGS[@]} > 0 )); then
  CMD+=("${EXTRA_ARGS[@]}")
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  printf '%q ' "${CMD[@]}"
  printf '\n'
  exit 0
fi

mkdir -p "${OUT_DIR}"
exec "${CMD[@]}"
