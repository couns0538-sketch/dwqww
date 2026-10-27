#!/usr/bin/env bash
# C5 Linux evidence (used by .github/workflows/opus-c4-nnue.yml after opus_round1/C4/ci_c4.sh):
#   1. lock replicas with 8 identical output heads through UCI (NNUEOutputBuckets 8, alone and with 8 mirrored
#      king buckets): bench x5 == the lock pins
#   2. CPU-torch smoke training of an 8-output-bucket net and a 4-king-bucket + 8-output-bucket net on synthetic
#      data32-style records, export parity on 10000 positions (every piece count 2..32, every output bucket)
# The output-bucket unit tests (every piece count 2..32) run in ci_c4.sh's forge_nnue_v2_tests.
# usage: opus_round1/C5/ci_c5.sh <out_dir> [<build_dir with forge and forge_nnue_v2_tool>]
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
BD=${2:-}
status=0
if [ -z "$BD" ]; then
  BD="$OUT/build"
  CXX=${CXX:-$(command -v g++-14 || command -v g++)}
  cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
    > "$OUT/configure.log" 2>&1 || { cat "$OUT/configure.log"; exit 1; }
  cmake --build "$BD" --target forge forge_nnue_v2_tool -j"$(nproc)" > "$OUT/build.log" 2>&1 || { tail -40 "$OUT/build.log"; exit 1; }
fi

echo "===== C5: lock replicas with 8 identical output heads through UCI (bench must equal the lock pins)"
LOCK="d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354"
for r in r1:0 rm8:8; do
  name=${r%%:*}; kb=${r##*:}
  python3 "$ROOT/tools/nnue/forge_nnue_v2.py" from-inc "$ROOT/src/nnue_weights.inc" "$OUT/lock_${name}_ob8.fnn2" \
    --replica "$name" --output-buckets 8 > /dev/null
  echo "-- replica $name + 8 output heads (NNUEKingBuckets $kb, NNUEOutputBuckets 8)"
  python3 "$ROOT/tools/nnue/bench_options.py" "$BD/forge" 11,13,16,20,22 --set "NNUEFile=$OUT/lock_${name}_ob8.fnn2" \
    --set "NNUEKingBuckets=$kb" --set NNUEOutputBuckets=8 --expect "$LOCK" 2>&1 | grep -E "bench|NNUE v2: active" | tee -a "$OUT/replica_ob_bench.log"
done
grep -q MISMATCH "$OUT/replica_ob_bench.log" && status=1
[ "$(grep -c ' OK' "$OUT/replica_ob_bench.log")" -eq 10 ] || status=1
# Replicas evaluate like the compiled-in net, so also require that the v2 path was active for both.
[ "$(grep -c 'NNUE v2: active' "$OUT/replica_ob_bench.log")" -eq 2 ] || { echo "v2 net not active"; status=1; }

echo "===== C5: smoke training (CPU torch) and export parity"
python3 -c "import torch, numpy; print('torch', torch.__version__, 'numpy', numpy.__version__)" || { echo "no torch: skipping"; exit $status; }
DATA="$OUT/data"; mkdir -p "$DATA"
(cd "$DATA" && python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" t 50000 50000 50000 50000 && \
 python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" h 50000) > "$OUT/data.log" 2>&1
"$BD/forge_nnue_v2_tool" positions "$OUT/parity_positions.fen" 10000 20261026
for cfg in "ob8:--output-buckets 8" "kb4ob8:--king-buckets 4 --output-buckets 8"; do
  name=${cfg%%:*}; extra=${cfg#*:}
  # shellcheck disable=SC2086
  python3 "$ROOT/tools/nnue/train_resid_v3b.py" --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" \
    --device cpu --residual --init-check --shape 256 --epochs 2 --lr 2e-3 --blend-end 0.6 --seed 20261027 \
    --batch-size 1024 --warmup-steps 30 --steps-per-epoch 150 --val-positions 16384 $extra \
    --run-dir "$OUT/smoke_$name" > "$OUT/smoke_$name.log" 2>&1 || { tail -20 "$OUT/smoke_$name.log"; status=1; continue; }
  grep -E "output buckets|king buckets|INIT CHECK|EPOCH|Saved" "$OUT/smoke_$name.log"
  NET=$(ls "$OUT/smoke_$name"/epoch002-*.fnn2)
  "$BD/forge_nnue_v2_tool" eval "$NET" "$OUT/parity_positions.fen" "$OUT/cpp_$name" || status=1
  python3 "$ROOT/tools/nnue/v2_parity.py" "${NET%.fnn2}.pt" "$NET" "$OUT/parity_positions.fen" "$OUT/cpp_$name" \
    --json "$OUT/parity_$name.json" 2>&1 | tee "$OUT/parity_$name.log"
  grep -q "^PASS" "$OUT/parity_$name.log" || status=1
done
rm -f "$OUT"/*.acc
echo "ci_c5 status=$status"
exit $status
