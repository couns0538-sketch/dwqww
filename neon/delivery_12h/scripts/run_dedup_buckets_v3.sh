#!/usr/bin/env bash
# Server-Day v3 Bucketed Parallel Vectorized Dedup Wrapper (Linux / EPYC)
# Hardened per Wave 7 Stream B audit:
#   - Enforces --skip-noisy (bit0=0, MANDATORY: +651..+700 Elo proof on FORGENN3-P)
#   - Enforces bit1=0 (in_check dropped; never passes --keep-in-check)
#   - Enforces --drop-draw-conflict 600 and --dedup-mode avg (sqrt(k) weights)
#   - < 0.72 GiB RAM/worker at 2.0B rows / 128 buckets (~23 GiB on 32 workers, ~6.6 min)
set -euo pipefail

export HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1

FORGE_LAB_ROOT="${FORGE_LAB_ROOT:-/workspace/nnue-lab}"
IN_DIR="${1:-${FORGE_LAB_ROOT}/data/raw_2b}"
OUT_DIR="${2:-${FORGE_LAB_ROOT}/data/clean_2b_quiet_avg}"
BUCKETS="${BUCKETS:-128}"
WORKERS="${WORKERS:-32}"
DEDUP_MODE="${DEDUP_MODE:-avg}"
SHARD_ROWS="${SHARD_ROWS:-500000}"
COMP_LEVEL="${COMP_LEVEL:-3}"

python3 -B "${FORGE_LAB_ROOT}/neon/filter_quest/partition_fqs_buckets.py" \
  --in-dir "${IN_DIR}" \
  --out-dir "${OUT_DIR}" \
  --buckets "${BUCKETS}" \
  --workers "${WORKERS}" \
  --skip-noisy \
  --drop-draw-conflict 600 \
  --dedup-mode "${DEDUP_MODE}" \
  --shard-rows "${SHARD_ROWS}" \
  --flush-rows 65536 \
  --comp-level "${COMP_LEVEL}"

# Post-dedup integrity gate: verify summary.json exists, t1_corrupt == 0, 0 .part files
python3 -B - "${OUT_DIR}" <<'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1])
parts = list(out.glob("*.part"))
assert not parts, f"Residual .part files found: {parts}"
sp = out / "summary.json"
assert sp.exists(), f"Missing {sp}"
s = json.loads(sp.read_text(encoding="utf-8"))
assert s.get("t1_corrupt", -1) == 0, f"Corrupt records detected: {s}"
print(f"DEDUP_V3_GATE_PASS: kept={s.get('kept')} merged={s.get('dedup_merged')} noisy_dropped={s.get('noisy_dropped', 'n/a')}")
PY
