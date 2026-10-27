#!/usr/bin/env bash
# S31 PC runner: average the last k epoch checkpoints of ONE trainer run and score every arm on the same holdout.
# Reads the run directory read-only (copies its last k .pt files plus the last .inc as the template), writes only to
# a NEW output directory, runs at Idle priority with one thread. Never names or starts a trainer process.
# usage: run_s31_pc.sh <run_dir> <k> <out_dir> <holdout.pos> <hce_dir> <fens_10k.txt> <lock_src_tree> <nnue_check.cpp>
# e.g.   run_s31_pc.sh F:/forge_nnue_train/runs/resid_h256_e48_f006_bs16k_lr10e4_b06_s25_fb8k 4 F:/opus_scratch/s31_f006 \
#          F:/opus_scratch/sol_S31/inputs/prod/holdout_013_014_s16.pos F:/opus_scratch/sol_S31/inputs/prod \
#          F:/opus_scratch/sol_S31/inputs/fens_10k.txt <lock>/1_source/forge_AL1_s198_src <lock>/5_nnue/tools/nnue_check.cpp
set -euo pipefail
RUN=$1; K=$2; OUT=$3; POS=$4; HCE=$5; FENS=$6; LOCK=$7; HARNESS=$8
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
[ -e "$OUT" ] && { echo "out dir exists: $OUT"; exit 2; }
mkdir -p "$OUT/ckpt" "$OUT/arms" "$OUT/tmp"
export TMP="$OUT/tmp" TEMP="$OUT/tmp"
mapfile -t PTS < <(ls "$RUN"/epoch*-step*.pt | sort | tail -n "$K")
[ "${#PTS[@]}" -ge 2 ] || { echo "need at least 2 .pt files"; exit 2; }
LAST_INC="${PTS[-1]%.pt}.inc"
for f in "${PTS[@]}" "$LAST_INC"; do cp -p "$f" "$OUT/ckpt/"; done
(cd "$RUN" && sha256sum $(for f in "${PTS[@]}" "$LAST_INC"; do basename "$f"; done)) > "$OUT/ckpt/SHA256_source.txt"
(cd "$OUT/ckpt" && sha256sum -c --quiet SHA256_source.txt)
TEMPLATE="$OUT/ckpt/$(basename "$LAST_INC")"
NETS=("$TEMPLATE")
for ((n = 2; n <= ${#PTS[@]}; n++)); do
  sel=(); for f in "${PTS[@]: -$n}"; do sel+=("$OUT/ckpt/$(basename "$f")"); done
  nice -n 19 "$PY" -I -B "$HERE/forge_sol_S31_avg_ckpt.py" avg --pts "${sel[@]}" --template "$TEMPLATE" --out "$OUT/arms/avg$n.inc"
  NETS+=("$OUT/arms/avg$n.inc")
done
nice -n 19 "$PY" -I -B "$HERE/forge_sol_S31_avg_ckpt.py" score --nets "${NETS[@]}" --pos "$POS" --hce-dir "$HCE" --out "$OUT/score.json"
nice -n 19 "$PY" -I -B "$HERE/forge_sol_S31_avg_ckpt.py" parity --nets "${NETS[@]:1}" --fens "$FENS" --lock-tree "$LOCK" \
  --harness "$HARNESS" --work "$OUT/parity" --out "$OUT/parity.json"
echo "done: $OUT/score.json $OUT/parity.json"
