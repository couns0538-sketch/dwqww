#!/usr/bin/env bash
set -euo pipefail

# CPU-only environment for 128-bucket 64-worker FQS1 dedup
export HIP_VISIBLE_DEVICES=""
export CUDA_VISIBLE_DEVICES=""
export ROCR_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1

LAB_ROOT="${LAB_ROOT:-${FORGE_LAB_ROOT:-/workspace/nnue-lab}}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
IN_DIR="${IN_DIR:-${LAB_ROOT}/data/raw_2b}"
OUT_DIR="${OUT_DIR:-${LAB_ROOT}/data/clean_2b_avg}"
DRY_RUN="${DRY_RUN:-0}"

EXTRA_ARGS=()
for arg in "$@"; do
  if [[ "${arg}" == "--dry-run" ]]; then
    DRY_RUN=1
  else
    EXTRA_ARGS+=("${arg}")
  fi
done

SCRIPT_PATH="${LAB_ROOT}/neon/filter_quest/partition_fqs_buckets.py"

CMD=(
  "${PYTHON_BIN}" -B "${SCRIPT_PATH}"
  --in-dir "${IN_DIR}"
  --out-dir "${OUT_DIR}"
  --buckets 128
  --workers 64
  --dedup-mode avg
  --drop-draw-conflict 600
  --shard-rows 500000
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
