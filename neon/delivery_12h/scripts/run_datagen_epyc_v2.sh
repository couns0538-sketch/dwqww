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
export FORGE_LAB_ROOT="${LAB_ROOT}"
export PYTHONPATH="${LAB_ROOT}/pipeline${PYTHONPATH:+:${PYTHONPATH}}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
OUT_DIR="${OUT_DIR:-${LAB_ROOT}/data/raw_2b}"
BOOK="${BOOK:-${LAB_ROOT}/neon/forge_fixes/book_cc0_clean.epd}"
CONFIG="${CONFIG:-${LAB_ROOT}/pipeline/config.forge.toml}"
TABLEBASE_DIR="${SYZYGY_DIR:-${TABLEBASE_DIR:-${LAB_ROOT}/tablebases/syzygy345}}"
EXE="${EXE:-${LAB_ROOT}/builds/v3p_engine}"
NET="${NET:-${LAB_ROOT}/runs/forge/r0067/train/cand.fnn3}"

POSITIONS="${POSITIONS:-2500000000}"
SHARD_SIZE="${SHARD_SIZE:-500000}"
SOFT_NODES="${SOFT_NODES:-4000}"
WRITE_MIN_PLY="${WRITE_MIN_PLY:-2}"
RANDOM_PLIES="${RANDOM_PLIES:-2}"
STARTPOS_FRAC="${STARTPOS_FRAC:-0.10}"
WIDE_DIV_FRAC="${WIDE_DIV_FRAC:-0.15}"
MAX_TEMP_C="${MAX_TEMP_C:-90.0}"
WORKERS="${WORKERS:-128}"
SEED="${SEED:-20261130}"
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
    --syzygy-dir)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --syzygy-dir requires a directory argument" >&2
        exit 2
      fi
      TABLEBASE_DIR="$2"
      shift 2
      ;;
    --syzygy-dir=*)
      TABLEBASE_DIR="${1#*=}"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: run_datagen_epyc_v2.sh [--dry-run] [--out-dir <dir>] [--syzygy-dir <dir>] [gen_cc0_selfgame_fqs.py args...]
Env overrides: LAB_ROOT/FORGE_LAB_ROOT, PYTHON_BIN, OUT_DIR, BOOK, CONFIG,
  SYZYGY_DIR/TABLEBASE_DIR, EXE, NET, POSITIONS, SHARD_SIZE, SOFT_NODES,
  WRITE_MIN_PLY, RANDOM_PLIES, STARTPOS_FRAC, WIDE_DIV_FRAC, MAX_TEMP_C,
  WORKERS, SEED, RESUME (1|0), DRY_RUN (1|0).
EOF
      exit 0
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

SCRIPT_PATH="${LAB_ROOT}/neon/forge_fixes/gen_cc0_selfgame_fqs.py"

CMD=(
  "${PYTHON_BIN}" -B "${SCRIPT_PATH}"
  --out-dir "${OUT_DIR}"
  --book "${BOOK}"
  --config "${CONFIG}"
  --tablebase-dir "${TABLEBASE_DIR}"
  --exe "${EXE}"
  --net "${NET}"
  --positions "${POSITIONS}"
  --shard-size "${SHARD_SIZE}"
  --soft-nodes "${SOFT_NODES}"
  --write-min-ply "${WRITE_MIN_PLY}"
  --random-plies "${RANDOM_PLIES}"
  --startpos-frac "${STARTPOS_FRAC}"
  --wide-div-frac "${WIDE_DIV_FRAC}"
  --drop-draw-conflicts
  --max-temp-c "${MAX_TEMP_C}"
  --workers "${WORKERS}"
  --seed "${SEED}"
)

if [[ "${RESUME}" == "1" ]]; then
  CMD+=(--resume)
fi

if (( ${#EXTRA_ARGS[@]} > 0 )); then
  CMD+=("${EXTRA_ARGS[@]}")
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  printf '%q ' "${CMD[@]}"
  printf '\n'
  exit 0
fi

mkdir -p "${OUT_DIR}"
"${CMD[@]}"

# Post-run FQS1 shard parity & integrity check (gen_cc0_selfgame_fqs.py summary.json omits white_stm)
"${PYTHON_BIN}" -B - "${OUT_DIR}" <<'PY'
import json
import sys
import zlib
from pathlib import Path
import numpy as np

out_dir = Path(sys.argv[1])
parts = sorted(out_dir.glob("*.part"))
if parts:
    raise SystemExit(f"Leftover .part files in {out_dir}: {[p.name for p in parts[:5]]}")

summary_path = out_dir / "summary.json"
if not summary_path.is_file():
    raise SystemExit(f"Missing summary.json in {out_dir}")
summary = json.loads(summary_path.read_text(encoding="utf-8"))

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])
shards = sorted(list(out_dir.glob("*.fqs.z")) + list(out_dir.glob("*.fqs")))
if not shards:
    raise SystemExit(f"No .fqs/.fqs.z shards found in {out_dir}")

total = 0
white = 0
for sp in shards:
    raw = sp.read_bytes()
    if sp.name.endswith(".z"):
        raw = zlib.decompress(raw)
    if len(raw) < 8 or raw[:8] != FQS_MAGIC or (len(raw) - 8) % FQS_DTYPE.itemsize != 0:
        raise SystemExit(f"Corrupt FQS1 shard: {sp}")
    arr = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8)
    stm = arr["stm"]
    if not np.all((stm == 0) | (stm == 1)):
        raise SystemExit(f"Invalid stm values in {sp}")
    total += int(len(arr))
    white += int((stm == 0).sum())

if total <= 0:
    raise SystemExit(f"Zero records across shards in {out_dir}")

white_stm_pct = 100.0 * white / total
if not (47.0 <= white_stm_pct <= 53.0):
    raise SystemExit(f"white_stm_pct={white_stm_pct:.2f}% outside [47.0%, 53.0%]")
print(
    f"PARITY_CHECK_PASS: shards={len(shards)} total={total} white={white} "
    f"white_stm_pct={white_stm_pct:.2f}% summary_positions={summary.get('positions')}",
    flush=True,
)
PY
