#!/usr/bin/env bash
set -euo pipefail

# CPU-only environment for EPYC self-play datagen (zero GPU usage)
export HIP_VISIBLE_DEVICES=""
export CUDA_VISIBLE_DEVICES=""
export ROCR_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1

LAB_ROOT="${LAB_ROOT:-${FORGE_LAB_ROOT:-/workspace/nnue-lab}}"
export PYTHONPATH="${LAB_ROOT}/pipeline${PYTHONPATH:+:${PYTHONPATH}}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUT_DIR="${OUT_DIR:-${LAB_ROOT}/data/raw_2b}"
BOOK="${BOOK:-${LAB_ROOT}/neon/forge_fixes/book_cc0_clean.epd}"
CONFIG="${CONFIG:-${LAB_ROOT}/pipeline/config.forge.toml}"
EXE="${EXE:-${LAB_ROOT}/builds/v3p_engine}"
NET="${NET:-${LAB_ROOT}/runs/forge/r0067/train/cand.fnn3}"

POSITIONS="${POSITIONS:-2500000000}"
SOFT_NODES="${SOFT_NODES:-4000}"
EVAL_LIMIT="${EVAL_LIMIT:-2000}"
MAX_PLY="${MAX_PLY:-300}"
WRITE_MIN_PLY="${WRITE_MIN_PLY:-2}"
RANDOM_PLIES="${RANDOM_PLIES:-2}"
STARTPOS_FRAC="${STARTPOS_FRAC:-0.10}"
MAX_ABS_SCORE="${MAX_ABS_SCORE:-1500}"
CONFLICT_SCORE="${CONFLICT_SCORE:-600}"
SHARD_ROWS="${SHARD_ROWS:-500000}"
WORKERS="${WORKERS:-128}"
SEED="${SEED:-20261130}"
DRY_RUN="${DRY_RUN:-0}"

EXTRA_ARGS=()
for arg in "$@"; do
  if [[ "${arg}" == "--dry-run" ]]; then
    DRY_RUN=1
  else
    EXTRA_ARGS+=("${arg}")
  fi
done

SCRIPT_PATH="${LAB_ROOT}/neon/forge_fixes/teamwork_wave2/streamB_nnue/gen_cc0_selfgame_fqs_v2.py"

CMD=(
  "${PYTHON_BIN}" -B "${SCRIPT_PATH}"
  --out-dir "${OUT_DIR}"
  --book "${BOOK}"
  --config "${CONFIG}"
  --exe "${EXE}"
  --net "${NET}"
  --positions "${POSITIONS}"
  --soft-nodes "${SOFT_NODES}"
  --eval-limit "${EVAL_LIMIT}"
  --max-ply "${MAX_PLY}"
  --write-min-ply "${WRITE_MIN_PLY}"
  --random-plies "${RANDOM_PLIES}"
  --startpos-frac "${STARTPOS_FRAC}"
  --max-abs-score "${MAX_ABS_SCORE}"
  --conflict-score "${CONFLICT_SCORE}"
  --shard-rows "${SHARD_ROWS}"
  --workers "${WORKERS}"
  --seed "${SEED}"
  --mem-need-gb 0
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
