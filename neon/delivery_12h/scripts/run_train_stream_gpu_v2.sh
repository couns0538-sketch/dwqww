#!/usr/bin/env bash
set -euo pipefail

# Portable lab root for Linux GPU training (set KEEP_VISIBLE_DEVICES=1 to preserve explicit GPU masks)
export FORGE_LAB_ROOT="${FORGE_LAB_ROOT:-${LAB_ROOT:-/workspace/nnue-lab}}"
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
GUARDS_PATH="${GUARDS_PATH:-${FORGE_LAB_ROOT}/neon/forge_fixes/teamwork_wave4/streamB_linux_serverday/linux_guards.py}"

CHECK_RAM_GB="${CHECK_RAM_GB:-16}"
KEEP_RAM_GB="${KEEP_RAM_GB:-5}"
SKIP_GUARDS="${SKIP_GUARDS:-0}"

DISTILL_NET="${DISTILL_NET-${FORGE_LAB_ROOT}/neon/forge_fixes/gpu_runs/G2_v3p_1024_pairwise_psqt/cand.pt}"
DISTILL_WEIGHT="${DISTILL_WEIGHT:-0.2}"
HIDDEN="${HIDDEN:-1024}"
KING_BUCKETS="${KING_BUCKETS:-8}"
SHARDS_PER_SB="${SHARDS_PER_SB:-400}"
ANCHOR_REPEAT="${ANCHOR_REPEAT:-25}"
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
RESUME="${RESUME:-1}"
DRY_RUN="${DRY_RUN:-0}"

EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --out-dir)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --out-dir requires a directory argument" >&2
        exit 2
      fi
      OUT_DIR="$2"
      shift 2
      ;;
    --out-dir=*)
      OUT_DIR="${1#*=}"
      shift
      ;;
    --hidden)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --hidden requires a value (1024 or 1536)" >&2
        exit 2
      fi
      HIDDEN="$2"
      shift 2
      ;;
    --hidden=*)
      HIDDEN="${1#*=}"
      shift
      ;;
    --king-buckets)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --king-buckets requires a value (8 or 16)" >&2
        exit 2
      fi
      KING_BUCKETS="$2"
      shift 2
      ;;
    --king-buckets=*)
      KING_BUCKETS="${1#*=}"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: run_train_stream_gpu_v2.sh [--dry-run] [--out-dir <dir>] [--hidden 1024|1536] [--king-buckets 8|16] [train_v3p_stream.py args...]
Env overrides: FORGE_LAB_ROOT/LAB_ROOT, PYTHON_BIN, FQS_SHARDS, OUT_DIR, ANCHOR_DIR, GUARDS_PATH,
  CHECK_RAM_GB, KEEP_RAM_GB, SKIP_GUARDS (0|1), DISTILL_NET, DISTILL_WEIGHT,
  HIDDEN (1024|1536), KING_BUCKETS (8|16), SHARDS_PER_SB, ANCHOR_REPEAT, EPOCHS,
  BATCH_SIZE, LR, MIN_LR_FRAC, WARMUP_STEPS, LR_CYCLES, W1_DECAY, OB_SMOOTH, MIX,
  LOSS_POW, SEED, RESUME (1|0), KEEP_VISIBLE_DEVICES (0|1), DRY_RUN (1|0).
EOF
      exit 0
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "${HIDDEN}" != "1024" && "${HIDDEN}" != "1536" ]]; then
  echo "ERROR: --hidden / HIDDEN must be 1024 or 1536 (got '${HIDDEN}')" >&2
  exit 2
fi
if [[ "${KING_BUCKETS}" != "8" && "${KING_BUCKETS}" != "16" ]]; then
  echo "ERROR: --king-buckets / KING_BUCKETS must be 8 or 16 (got '${KING_BUCKETS}')" >&2
  exit 2
fi

SCRIPT_PATH="${FORGE_LAB_ROOT}/neon/forge_fixes/train_v3p_stream.py"

GUARD_STATUS_CMD=(
  "${PYTHON_BIN}" -B "${GUARDS_PATH}"
  --status
)

GUARD_RAM_CMD=(
  "${PYTHON_BIN}" -B "${GUARDS_PATH}"
  --check-ram-gb "${CHECK_RAM_GB}"
  --keep-ram-gb "${KEEP_RAM_GB}"
)

# Note: --save-ckpt-every is intentionally omitted because train_v3p_stream.py does not
# define that flag. Instead, train_v3p_stream.py automatically saves resume_ckpt.pt
# atomically (tmp_resume_ckpt.pt -> os.replace) after every superbatch, while --save-cycles
# writes cand_e{ep}.pt at each cosine LR cycle boundary.
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
  --king-buckets "${KING_BUCKETS}"
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
  --save-cycles
  --seed "${SEED}"
  --mem-need-gb 0
  --out-dir "${OUT_DIR}"
)

if [[ -n "${DISTILL_NET}" ]]; then
  CMD+=(--distill-net "${DISTILL_NET}" --distill-weight "${DISTILL_WEIGHT}")
fi

if [[ "${RESUME}" == "1" ]]; then
  CMD+=(--resume)
fi

if (( ${#EXTRA_ARGS[@]} > 0 )); then
  CMD+=("${EXTRA_ARGS[@]}")
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  if [[ "${SKIP_GUARDS}" != "1" ]]; then
    printf '%q ' "${GUARD_STATUS_CMD[@]}"
    printf '\n'
    printf '%q ' "${GUARD_RAM_CMD[@]}"
    printf '\n'
  fi
  printf '%q ' "${CMD[@]}"
  printf '\n'
  exit 0
fi

if [[ "${SKIP_GUARDS}" != "1" ]]; then
  "${GUARD_STATUS_CMD[@]}"
  "${GUARD_RAM_CMD[@]}"
fi

mkdir -p "${OUT_DIR}"
exec "${CMD[@]}"
