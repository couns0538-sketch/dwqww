#!/usr/bin/env bash
# O4 Linux evidence (.github/workflows/opus-o4-nnue.yml; also runnable on a Linux box with python3 + numpy + torch):
#   1. build (box recipe flags, CMake Release): forge, forge_pure_nnue_tests, forge_nnue_engine_eval and C4's v2
#      tests/tool; the AL1 s198 lock tree (git 294dbed) for the NPS comparison
#   2. tests: forge_pure_nnue_tests (PureNnue rules, network-only evaluation on 4 x 25000-ply walks, search, UCI),
#      C4's forge_nnue_v2_tests (102k plies) and forge_nnue_v2_uci_tests (regression of the C4 path)
#   3. options off: bench x5 + perft + kiwipete exact (uci_check --full); C4's lock replicas r1 and rm8 through UCI:
#      bench x5 == the lock pins (the residual v2 path is unchanged)
#   4. trainer --pure (CPU torch): archive-style synthetic records with .hce (tools/nnue/mkdata_data32_synthetic.py)
#      and material-labelled records without .hce (opus_round1/O4/mkdata_material.py); export parity on the 10000
#      positions of opus_round1/C4/parity_positions.fen (tools/nnue/v2_parity.py: PyTorch == C++ network, bit for
#      bit) and the engine's PureNnue evaluation == the network alone (forge_nnue_engine_eval); planted trainer bug
#   5. evaluation cost on identical 3M-ply walks (forge_nnue_engine_eval --walk): the lock weights + HCE (replica
#      r1, residual) vs the same weights flagged stand-alone with PureNnue (difference = the HCE), and the
#      compiled-in default path; 3 interleaved rounds
#   6. NPS, bench 16 / 20, Threads 1, Hash 16, ABBA in fresh processes (opus_round1/C4/nps_ab_options.py): lock vs
#      O4 options off (identical nodes required), and O4 off vs O4 PureNnue with the material-trained pure net
#      (another evaluation searches another tree: nodes are reported)
# usage: opus_round1/O4/ci_o4.sh <out_dir>
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
cmake --build "$BD" --target forge forge_pure_nnue_tests forge_nnue_engine_eval forge_nnue_v2_tests forge_nnue_v2_uci_tests \
  forge_nnue_v2_tool -j"$(nproc)" > "$OUT/build.log" 2>&1 || { tail -40 "$OUT/build.log"; exit 1; }
echo "compiler: $($CXX --version | head -1)"
echo "forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)  FMA count: $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)"
mkdir -p "$OUT/lock_src"
(cd "$ROOT" && git archive 294dbed | tar -x -m -C "$OUT/lock_src")
cmake -S "$OUT/lock_src" -B "$OUT/build_lock" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
  "-DCMAKE_CXX_FLAGS=$FL" > "$OUT/configure_lock.log" 2>&1 && \
  cmake --build "$OUT/build_lock" --target forge -j"$(nproc)" > "$OUT/build_lock.log" 2>&1 || { tail -20 "$OUT/build_lock.log"; status=1; }

step "tests"
(cd "$OUT" && timeout 1500 "$BD/forge_pure_nnue_tests" "$BD/forge" 25000) > "$OUT/pure_nnue_tests.log" 2>&1 || status=1
grep -E "^(FAIL|WALK)|checks passed" "$OUT/pure_nnue_tests.log"
(cd "$OUT" && timeout 900 "$BD/forge_nnue_v2_tests") > "$OUT/nnue_v2_tests.log" 2>&1 || status=1
grep -E "^(FAIL|WALK)|checks passed" "$OUT/nnue_v2_tests.log"
(cd "$OUT" && timeout 300 "$BD/forge_nnue_v2_uci_tests" "$BD/forge") > "$OUT/nnue_v2_uci_tests.log" 2>&1 || status=1
grep -E "^FAIL|checks passed" "$OUT/nnue_v2_uci_tests.log"

step "options off: identity (O4 and the lock build); C4's lock replicas through UCI"
python3 "$ROOT/opus_round1/ci/uci_check.py" "$BD/forge" --full 2>&1 | tee "$OUT/identity_off.log"
grep -q "ALL OK" "$OUT/identity_off.log" || status=1
python3 "$ROOT/opus_round1/ci/uci_check.py" "$OUT/build_lock/forge" 2>&1 | tee "$OUT/identity_lock_build.log"
grep -q "ALL OK" "$OUT/identity_lock_build.log" || status=1
LOCK="d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354"
for r in r1:1 rm8:8; do
  name=${r%%:*}; kb=${r##*:}
  python3 "$ROOT/tools/nnue/forge_nnue_v2.py" from-inc "$ROOT/src/nnue_weights.inc" "$OUT/lock_$name.fnn2" --replica "$name" > /dev/null
  echo "-- replica $name (NNUEKingBuckets $kb)"
  python3 "$ROOT/tools/nnue/bench_options.py" "$BD/forge" 11,13,16,20,22 --set "NNUEFile=$OUT/lock_$name.fnn2" \
    --set "NNUEKingBuckets=$kb" --expect "$LOCK" 2>&1 | grep -E "bench|NNUE v2|ENGINE" | tee -a "$OUT/replica_bench.log" || status=1
done
grep -q "MISMATCH\|ENGINE FAILED" "$OUT/replica_bench.log" && status=1
[ "$(grep -c ' OK$' "$OUT/replica_bench.log")" -eq 10 ] || { echo "replica benches missing"; status=1; }

step "trainer --pure (CPU torch), export parity on 10000 positions, the engine's PureNnue evaluation"
python3 -c "import torch, numpy; print('torch', torch.__version__, 'numpy', numpy.__version__)" || { echo "no torch"; exit 1; }
DATA="$OUT/data"; MAT="$OUT/material"; mkdir -p "$DATA" "$MAT"
(cd "$DATA" && python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" t 50000 50000 50000 50000 && \
 python3 "$ROOT/tools/nnue/mkdata_data32_synthetic.py" h 50000) > "$OUT/data.log" 2>&1
(cd "$MAT" && python3 "$ROOT/opus_round1/O4/mkdata_material.py" t 50000 50000 50000 50000 && \
 python3 "$ROOT/opus_round1/O4/mkdata_material.py" h 50000) 2>&1 | tee "$OUT/material_data.log"
FENS="$ROOT/opus_round1/C4/parity_positions.fen"
TR="$ROOT/tools/nnue/train_resid_v3b.py"
train() { # name script args...
  local name=$1 script=$2; shift 2
  python3 "$script" "$@" --run-dir "$OUT/$name" > "$OUT/$name.log" 2>&1 || { tail -20 "$OUT/$name.log"; status=1; }
  grep -E "BASELINE|train:|steps/epoch|EPOCH|FINAL|Finished" "$OUT/$name.log"
}
echo "-- trainer default paths == C4's trainer (d9a73ab3), byte-identical outputs"
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
  train "o4_id_${id}_new" "$TR" --train "$DATA/t0*.pos" $COMMON $extra > /dev/null
  # shellcheck disable=SC2086
  train "o4_id_${id}_c4" "$OUT/c4ref/trainer_c4.py" --train "$DATA/t0*.pos" $COMMON $extra > /dev/null
  if [ "$(outputs "$OUT/o4_id_${id}_new" | sha256sum)" = "$(outputs "$OUT/o4_id_${id}_c4" | sha256sum)" ] &&
     [ "$(normlog "$OUT/o4_id_${id}_new.log" | sha256sum)" = "$(normlog "$OUT/o4_id_${id}_c4.log" | sha256sum)" ] &&
     [ "$(outputs "$OUT/o4_id_${id}_new" | wc -l)" -ge 3 ] && ! grep -q "^train: 0 positions" "$OUT/o4_id_${id}_new.log"; then
    echo "IDENTICAL ($extra): $(outputs "$OUT/o4_id_${id}_new" | wc -l) output files and the normalised log" | tee -a "$OUT/trainer_default_identity.log"
  else
    echo "DIFFERENT ($extra)" | tee -a "$OUT/trainer_default_identity.log"; status=1
  fi
done
train o4_sample "$TR" --pure --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" --device cpu --shape 256 \
  --epochs 3 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 --steps-per-epoch 200 \
  --val-positions 16384 --final-full-val
train o4_material "$TR" --pure --train "$MAT/t0*.pos" --holdout "$MAT/h000.pos" --device cpu --shape 256 --epochs 4 \
  --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 --steps-per-epoch 195 --val-positions 16384
for name in o4_sample o4_material; do
  NET=$(ls "$OUT/$name"/epoch00[34]-*.fnn2 | tail -1)
  echo "-- $name: $(basename "$NET")"
  "$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$OUT/cpp_$name" || status=1
  python3 "$ROOT/tools/nnue/v2_parity.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$OUT/cpp_$name" --json "$OUT/parity_$name.json" \
    2>&1 | tee "$OUT/parity_$name.log"
  grep -q "^PASS" "$OUT/parity_$name.log" || status=1
  "$BD/forge_nnue_engine_eval" "$FENS" "$OUT/engine_$name.tsv" "NNUEFile=$NET" PureNnue=1 2>&1 | tee "$OUT/engine_$name.log"
  grep -q "^PASS" "$OUT/engine_$name.log" || status=1
done
echo "-- planted trainer bug: the pure net exported with the residual flag"
mkdir -p "$OUT/bug"
cp "$ROOT/tools/nnue/forge_nnue_v2.py" "$ROOT/tools/nnue/qa_adam_dml.py" "$OUT/bug/"
python3 - "$TR" "$OUT/bug/trainer_bug.py" <<'PY'
import sys
s = open(sys.argv[1], encoding="utf-8").read()
old = ("            if a.export_v2 or a.pure:  # O4: a pure net is used through NNUEFile + PureNnue, i.e. as a v2 file\n"
       "                export_forge_v2(model, stem, bool(a.residual))")
assert s.count(old) == 1
open(sys.argv[2], "w", encoding="utf-8").write(s.replace(old, old.replace("bool(a.residual))", "True)")))
PY
train o4_bug "$OUT/bug/trainer_bug.py" --pure --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" --device cpu \
  --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 10 --steps-per-epoch 40 \
  --val-positions 8192
NET=$(ls "$OUT/o4_bug"/epoch001-*.fnn2)
"$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$OUT/cpp_o4_bug" > /dev/null
python3 "$ROOT/tools/nnue/v2_parity.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$OUT/cpp_o4_bug" > "$OUT/parity_o4_bug.log" 2>&1
grep -E "^export|^PASS|^FAIL" "$OUT/parity_o4_bug.log"
grep -q "^FAIL" "$OUT/parity_o4_bug.log" && echo "planted bug caught by the parity check" || { echo "planted bug NOT caught"; status=1; }
"$BD/forge_nnue_engine_eval" "$FENS" "$OUT/engine_o4_bug.tsv" "NNUEFile=$NET" PureNnue=1 > "$OUT/engine_o4_bug.log" 2>&1
rc=$?
cat "$OUT/engine_o4_bug.log"
[ "$rc" = 2 ] && echo "planted bug refused by the engine (exit 2)" || { echo "planted bug NOT refused (exit $rc)"; status=1; }

step "evaluation cost: identical 3M-ply walks (lock weights + HCE vs the same weights stand-alone with PureNnue)"
python3 "$ROOT/opus_round1/O4/standalone_copy.py" "$OUT/lock_r1.fnn2" "$OUT/lock_r1_standalone.fnn2"
for round in 1 2 3; do
  for cfg in default residual pure; do
    case $cfg in
      default) set -- ;;
      residual) set -- "NNUEFile=$OUT/lock_r1.fnn2" NNUEKingBuckets=1 ;;
      pure) set -- "NNUEFile=$OUT/lock_r1_standalone.fnn2" PureNnue=1 ;;
    esac
    echo "round $round $cfg: $("$BD/forge_nnue_engine_eval" --walk 3000000 20261027 "$@" | grep '^walk')" | tee -a "$OUT/eval_cost_walk.log"
  done
done

step "NPS (bench 16 / 20)"
python3 "$ROOT/opus_round1/C4/nps_ab_options.py" "$OUT/build_lock/forge" "$BD/forge" 10 16,20 --same-nodes 2>&1 | \
  tee "$OUT/nps_off_lock_vs_o4.log"
MATNET=$(ls "$OUT/o4_material"/epoch004-*.fnn2 | tail -1)
python3 "$ROOT/opus_round1/C4/nps_ab_options.py" "$BD/forge" "$BD/forge" 8 16,20 --b-set "NNUEFile=$MATNET" \
  --b-set "PureNnue=1" 2>&1 | tee "$OUT/nps_on_pure_material_vs_off.log"
rm -f "$OUT"/*.acc
echo "ci_o4 status=$status"
exit $status
