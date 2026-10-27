#!/usr/bin/env bash
# O6 Linux evidence (.github/workflows/opus-o6-nnue.yml; also runnable on a Linux box with python3 + numpy + torch):
#   1. build (box recipe flags, CMake Release): forge, forge_nnue_threat_tests and C4's v2 tests/tool; the AL1 s198
#      lock tree (git 294dbed) for the NPS comparison
#   2. tests: forge_nnue_threat_tests (threat pairs vs brute force, features, loader, NNUEThreats rules, zero-threat
#      lock replicas, incremental == refresh on 3 x 34000 plies, UCI) and C4's forge_nnue_v2_tests /
#      forge_nnue_v2_uci_tests (regression)
#   3. options off: bench x5 + perft + kiwipete exact (uci_check --full); through UCI, C4's lock replicas r1 / rm8
#      (NNUEKingBuckets) and the same replicas with a threat block of zeros (NNUEThreats 1): bench x5 == lock pins
#   4. trainer: default paths == C4's trainer (byte-identical outputs); --threats (1 bucket) and --threats
#      --king-buckets 4 on archive-style synthetic records; export parity on the 10000 positions of
#      opus_round1/C4/parity_positions.fen (tools/nnue/v2_parity.py: threat block, accumulators, output bit for bit);
#      a planted trainer bug (pawn attack directions swapped) must fail the parity
#   5. NPS, bench 16 / 20, Threads 1, Hash 16, ABBA in fresh processes (opus_round1/C4/nps_ab_options.py): lock vs
#      O6 options off (identical nodes), lock vs O6 NNUEThreats 1 with the zero-threat r1 replica (identical nodes:
#      the engine cost of threat inputs), lock vs O6 with the CPU-trained threat net (another tree: nodes reported)
# usage: opus_round1/O6/ci_o6.sh <out_dir>
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
FL="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
BD="$OUT/build"
status=0
step() { echo; echo "===== $*"; }
export PYTHONDONTWRITEBYTECODE=1
cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$FL" \
  > "$OUT/configure.log" 2>&1 || { cat "$OUT/configure.log"; exit 1; }
cmake --build "$BD" --target forge forge_nnue_threat_tests forge_nnue_v2_tests forge_nnue_v2_uci_tests forge_nnue_v2_tool \
  -j"$(nproc)" > "$OUT/build.log" 2>&1 || { tail -40 "$OUT/build.log"; exit 1; }
echo "compiler: $($CXX --version | head -1)"
echo "forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)  FMA count: $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)"
mkdir -p "$OUT/lock_src"
(cd "$ROOT" && git archive 294dbed | tar -x -m -C "$OUT/lock_src")
cmake -S "$OUT/lock_src" -B "$OUT/build_lock" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
  "-DCMAKE_CXX_FLAGS=$FL" > "$OUT/configure_lock.log" 2>&1 && \
  cmake --build "$OUT/build_lock" --target forge -j"$(nproc)" > "$OUT/build_lock.log" 2>&1 || { tail -20 "$OUT/build_lock.log"; status=1; }

step "tests"
(cd "$OUT" && timeout 1500 "$BD/forge_nnue_threat_tests" "$BD/forge" 34000) > "$OUT/threat_tests.log" 2>&1 || status=1
grep -E "^(FAIL|WALK)|checks passed|brute-force|replica" "$OUT/threat_tests.log"
(cd "$OUT" && timeout 900 "$BD/forge_nnue_v2_tests") > "$OUT/nnue_v2_tests.log" 2>&1 || status=1
grep -E "^(FAIL|WALK)|checks passed" "$OUT/nnue_v2_tests.log"
(cd "$OUT" && timeout 300 "$BD/forge_nnue_v2_uci_tests" "$BD/forge") > "$OUT/nnue_v2_uci_tests.log" 2>&1 || status=1
grep -E "^FAIL|checks passed" "$OUT/nnue_v2_uci_tests.log"

step "options off: identity; C4's lock replicas and zero-threat lock replicas through UCI"
python3 "$ROOT/opus_round1/ci/uci_check.py" "$BD/forge" --full 2>&1 | tee "$OUT/identity_off.log"
grep -q "ALL OK" "$OUT/identity_off.log" || status=1
python3 "$ROOT/opus_round1/ci/uci_check.py" "$OUT/build_lock/forge" 2>&1 | tee "$OUT/identity_lock_build.log"
grep -q "ALL OK" "$OUT/identity_lock_build.log" || status=1
LOCK="d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354"
for r in r1:1 rm8:8; do
  name=${r%%:*}; kb=${r##*:}
  python3 "$ROOT/tools/nnue/forge_nnue_v2.py" from-inc "$ROOT/src/nnue_weights.inc" "$OUT/lock_$name.fnn2" --replica "$name" > /dev/null
  python3 "$ROOT/tools/nnue/forge_nnue_v2.py" from-inc "$ROOT/src/nnue_weights.inc" "$OUT/lock_${name}_t0.fnn2" --replica "$name" \
    --threats-zero | tee -a "$OUT/replica_bench.log"
  echo "-- replica $name (NNUEKingBuckets $kb)" | tee -a "$OUT/replica_bench.log"
  python3 "$ROOT/tools/nnue/bench_options.py" "$BD/forge" 11,13,16,20,22 --set "NNUEFile=$OUT/lock_$name.fnn2" \
    --set "NNUEKingBuckets=$kb" --expect "$LOCK" 2>&1 | grep -E "bench|NNUE v2|ENGINE" | tee -a "$OUT/replica_bench.log" || status=1
  echo "-- replica $name + zero threat block (NNUEKingBuckets $kb, NNUEThreats 1)" | tee -a "$OUT/replica_bench.log"
  python3 "$ROOT/tools/nnue/bench_options.py" "$BD/forge" 11,13,16,20,22 --set "NNUEFile=$OUT/lock_${name}_t0.fnn2" \
    --set "NNUEKingBuckets=$kb" --set "NNUEThreats=1" --expect "$LOCK" 2>&1 | grep -E "bench|NNUE v2|ENGINE" | tee -a "$OUT/replica_bench.log" || status=1
done
grep -q "MISMATCH\|ENGINE FAILED" "$OUT/replica_bench.log" && status=1
[ "$(grep -c ' OK$' "$OUT/replica_bench.log")" -eq 20 ] || { echo "replica benches missing"; status=1; }
[ "$(grep -c 'active: .*threat inputs' "$OUT/replica_bench.log")" -ge 2 ] || { echo "zero-threat replica not active"; status=1; }

step "trainer: default paths, --threats training, export parity on 10000 positions, planted bug"
python3 -c "import torch, numpy; print('torch', torch.__version__, 'numpy', numpy.__version__)" || { echo "no torch"; exit 1; }
DATA="$OUT/data"; mkdir -p "$DATA"
(cd "$DATA" && python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" t 50000 50000 50000 50000 && \
 python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" h 50000) > "$OUT/data.log" 2>&1
FENS="$ROOT/opus_round1/C4/parity_positions.fen"
TR="$ROOT/tools/nnue/train_resid_v3b.py"
train() { # name script args...
  local name=$1 script=$2; shift 2
  python3 "$script" "$@" --run-dir "$OUT/$name" > "$OUT/$name.log" 2>&1 || { tail -20 "$OUT/$name.log"; status=1; }
  grep -E "threat inputs|INIT|train:|steps/epoch|EPOCH|Finished" "$OUT/$name.log"
}
mkdir -p "$OUT/c4ref"
(cd "$ROOT" && git show d9a73ab3:tools/nnue/train_resid_v3b.py) > "$OUT/c4ref/trainer_c4.py"
cp "$ROOT/tools/nnue/forge_nnue_v2.py" "$ROOT/tools/nnue/qa_adam_dml.py" "$OUT/c4ref/"
outputs() { (cd "$1" && find . -type f ! -name 'settings_*' | LC_ALL=C sort | xargs sha256sum); }
normlog() { sed -E 's/ in [0-9]+s / in Ns /; s/[0-9,]+ pos\/s/N pos\/s/; s/\([0-9]+s( load)?\)/(Ns\1)/; /^MEM /d; s/ in [0-9]+s$/ in Ns/' "$1"; }
COMMON="--holdout $DATA/h000.pos --hce-dir $DATA --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027
        --batch-size 1024 --warmup-steps 10 --steps-per-epoch 40 --val-positions 8192 --log-every 1000"
for c in "a:--residual --init-check --export-v2" "b:--export-v2" "c:--residual --king-buckets 4" "d:--residual --mmap-data --final-full-val"; do
  id=${c%%:*}; extra=${c#*:}
  # shellcheck disable=SC2086
  train "o6_id_${id}_new" "$TR" --train "$DATA/t0*.pos" $COMMON $extra > /dev/null
  # shellcheck disable=SC2086
  train "o6_id_${id}_c4" "$OUT/c4ref/trainer_c4.py" --train "$DATA/t0*.pos" $COMMON $extra > /dev/null
  if [ "$(outputs "$OUT/o6_id_${id}_new" | sha256sum)" = "$(outputs "$OUT/o6_id_${id}_c4" | sha256sum)" ] &&
     [ "$(normlog "$OUT/o6_id_${id}_new.log" | sha256sum)" = "$(normlog "$OUT/o6_id_${id}_c4.log" | sha256sum)" ] &&
     [ "$(outputs "$OUT/o6_id_${id}_new" | wc -l)" -ge 3 ] && ! grep -q "^train: 0 positions" "$OUT/o6_id_${id}_new.log"; then
    echo "IDENTICAL ($extra): $(outputs "$OUT/o6_id_${id}_new" | wc -l) output files and the normalised log" | tee -a "$OUT/trainer_default_identity.log"
  else
    echo "DIFFERENT ($extra)" | tee -a "$OUT/trainer_default_identity.log"; status=1
  fi
done
train o6_threats "$TR" --threats --residual --init-check --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" \
  --device cpu --shape 256 --epochs 2 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 \
  --steps-per-epoch 150 --val-positions 16384
train o6_threats_kb4 "$TR" --threats --king-buckets 4 --residual --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" \
  --hce-dir "$DATA" --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 \
  --warmup-steps 30 --steps-per-epoch 150 --val-positions 16384
for name in o6_threats o6_threats_kb4; do
  NET=$(ls "$OUT/$name"/epoch00*.fnn2 | tail -1)
  echo "-- $name: $(basename "$NET")"
  "$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$OUT/cpp_$name" || status=1
  python3 "$ROOT/tools/nnue/v2_parity.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$OUT/cpp_$name" --json "$OUT/parity_$name.json" \
    2>&1 | tee "$OUT/parity_$name.log"
  grep -q "^PASS" "$OUT/parity_$name.log" || status=1
done
echo "-- planted trainer bug: pawn attack directions swapped in the trainer's threat pairs"
mkdir -p "$OUT/bug"
cp "$ROOT/tools/nnue/forge_nnue_v2.py" "$ROOT/tools/nnue/qa_adam_dml.py" "$OUT/bug/"
python3 - "$TR" "$OUT/bug/trainer_bug.py" <<'PY'
import sys
s = open(sys.argv[1], encoding="utf-8").read()
old = "((kd == 2) & (a_l == 1)) |"
assert s.count(old) == 1
s = s.replace(old, "((kd == 2) & (a_l == 7)) |").replace("((kd == 3) & (a_l == 7)))", "((kd == 3) & (a_l == 1)))")
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
train o6_bug "$OUT/bug/trainer_bug.py" --threats --residual --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" \
  --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 10 \
  --steps-per-epoch 20 --val-positions 4096
NET=$(ls "$OUT/o6_bug"/epoch001-*.fnn2)
"$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$OUT/cpp_o6_bug" > /dev/null
# The PyTorch side of the parity must use the buggy trainer's feature function: a parity copy importing it.
sed 's/^import train_resid_v3b as T  # noqa: E402$/import trainer_bug as T  # noqa: E402/' "$ROOT/tools/nnue/v2_parity.py" > "$OUT/bug/parity_bug.py"
python3 "$OUT/bug/parity_bug.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$OUT/cpp_o6_bug" > "$OUT/parity_o6_bug.log" 2>&1
grep -E "^export|^acc|^output|^PASS|^FAIL" "$OUT/parity_o6_bug.log"
grep -q "^FAIL" "$OUT/parity_o6_bug.log" && echo "planted bug caught by the parity check" || { echo "planted bug NOT caught"; status=1; }

step "NPS (bench 16 / 20)"
python3 "$ROOT/opus_round1/C4/nps_ab_options.py" "$OUT/build_lock/forge" "$BD/forge" 10 16,20 --same-nodes 2>&1 | \
  tee "$OUT/nps_off_lock_vs_o6.log"
python3 "$ROOT/opus_round1/C4/nps_ab_options.py" "$OUT/build_lock/forge" "$BD/forge" 10 16,20 --same-nodes \
  --b-set "NNUEFile=$OUT/lock_r1_t0.fnn2" --b-set "NNUEKingBuckets=1" --b-set "NNUEThreats=1" 2>&1 | \
  tee "$OUT/nps_on_zero_threat_r1_vs_lock.log"
TNET=$(ls "$OUT/o6_threats"/epoch002-*.fnn2 | tail -1)
python3 "$ROOT/opus_round1/C4/nps_ab_options.py" "$OUT/build_lock/forge" "$BD/forge" 6 16,20 --b-set "NNUEFile=$TNET" \
  --b-set "NNUEKingBuckets=1" --b-set "NNUEThreats=1" 2>&1 | tee "$OUT/nps_on_cpu_threat_net_vs_lock.log"
rm -f "$OUT"/*.acc
echo "ci_o6 status=$status"
exit $status
