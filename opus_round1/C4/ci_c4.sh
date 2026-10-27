#!/usr/bin/env bash
# C4 Linux evidence (used by .github/workflows/opus-c4-nnue.yml; also runnable on a Linux box):
#   1. build (box recipe flags, CMake Release): forge, forge_nnue_v2_tests, forge_nnue_v2_tool
#   2. forge_nnue_v2_tests (bucket map, mirroring, loader, lock replicas, 102k-ply incremental == refresh)
#   3. options off: bench x5 + perft + kiwipete exact (uci_check --full)
#   4. lock replicas through UCI NNUEFile + NNUEKingBuckets: bench x5 == the lock pins
#   5. CPU-torch smoke training of 4- and 8-bucket mirrored nets on synthetic data32-style records
#      (tools/nnue/mkdata_data32_synthetic.py, the generator of 5_nnue/sample_data) and the export parity
#      on 10000 positions (tools/nnue/v2_parity.py)
# Needs python3 with numpy and torch for step 5.  usage: opus_round1/C4/ci_c4.sh <out_dir>
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
BD="$OUT/build"
status=0
step() { echo; echo "===== $*"; }
cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
  "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
  > "$OUT/configure.log" 2>&1 || { cat "$OUT/configure.log"; exit 1; }
cmake --build "$BD" --target forge forge_nnue_v2_tests forge_nnue_v2_tool -j"$(nproc)" > "$OUT/build.log" 2>&1 || { tail -40 "$OUT/build.log"; exit 1; }
echo "compiler: $($CXX --version | head -1)"
echo "forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)  FMA count: $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)"

step "unit tests (forge_nnue_v2_tests)"
(cd "$OUT" && timeout 900 "$BD/forge_nnue_v2_tests") > "$OUT/unit_tests.log" 2>&1 || status=1
grep -E "^(FAIL|WALK)|checks passed" "$OUT/unit_tests.log"

step "options off: identity"
python3 "$ROOT/opus_round1/ci/uci_check.py" "$BD/forge" --full 2>&1 | tee "$OUT/identity_off.log"
grep -q "ALL OK" "$OUT/identity_off.log" || status=1

step "lock replicas through UCI (bench must equal the lock pins)"
LOCK="d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354"
for r in r1:1 r4:4 rm2:2 rm8:8 rm16:16; do
  name=${r%%:*}; kb=${r##*:}
  python3 "$ROOT/tools/nnue/forge_nnue_v2.py" from-inc "$ROOT/src/nnue_weights.inc" "$OUT/lock_$name.fnn2" --replica "$name" > /dev/null
  echo "-- replica $name (NNUEKingBuckets $kb)"
  python3 "$ROOT/tools/nnue/bench_options.py" "$BD/forge" 11,13,16,20,22 --set "NNUEFile=$OUT/lock_$name.fnn2" \
    --set "NNUEKingBuckets=$kb" --expect "$LOCK" 2>&1 | grep -E "bench|NNUE v2" | tee -a "$OUT/replica_bench.log" || status=1
done
grep -q MISMATCH "$OUT/replica_bench.log" && status=1

step "smoke training (CPU torch) and export parity"
python3 -c "import torch, numpy; print('torch', torch.__version__, 'numpy', numpy.__version__)" || { echo "no torch: skipping"; exit $status; }
DATA="$OUT/data"; mkdir -p "$DATA"
(cd "$DATA" && python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" t 50000 50000 50000 50000 && \
 python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" h 50000) > "$OUT/data.log" 2>&1
"$BD/forge_nnue_v2_tool" positions "$OUT/parity_positions.fen" 10000 20261026
for kb in 4 8; do
  python3 "$ROOT/tools/nnue/train_resid_v3b.py" --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" \
    --device cpu --residual --init-check --shape 256 --epochs 2 --lr 2e-3 --blend-end 0.6 --seed 20261026 \
    --batch-size 1024 --warmup-steps 30 --steps-per-epoch 150 --val-positions 16384 --king-buckets $kb \
    --run-dir "$OUT/smoke_kb$kb" > "$OUT/smoke_kb$kb.log" 2>&1 || { tail -20 "$OUT/smoke_kb$kb.log"; status=1; continue; }
  grep -E "king buckets|INIT CHECK|EPOCH|Saved" "$OUT/smoke_kb$kb.log"
  NET=$(ls "$OUT/smoke_kb$kb"/epoch002-*.fnn2)
  "$BD/forge_nnue_v2_tool" eval "$NET" "$OUT/parity_positions.fen" "$OUT/cpp_kb$kb" || status=1
  python3 "$ROOT/tools/nnue/v2_parity.py" "${NET%.fnn2}.pt" "$NET" "$OUT/parity_positions.fen" "$OUT/cpp_kb$kb" \
    --json "$OUT/parity_kb$kb.json" 2>&1 | tee "$OUT/parity_kb$kb.log"
  grep -q "^PASS" "$OUT/parity_kb$kb.log" || status=1
done
rm -f "$OUT"/*.acc
echo "ci_c4 status=$status"
exit $status
