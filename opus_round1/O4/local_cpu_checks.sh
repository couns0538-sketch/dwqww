#!/usr/bin/env bash
# O4 local CPU checks on the shared Windows PC (trainer + export parity), run as the user's NNUE rules require:
#   - CPU torch from the read-only venv, one thread (opus_nnue_smoke_run1t.py), nice 19, free-RAM guard 6 GB;
#   - every Python script that runs is a renamed copy called opus_nnue_smoke*.py: opus_nnue_smoke.py = this
#     branch's tools/nnue/train_resid_v3b.py, opus_nnue_smoke_c4ref.py = C4's (d9a73ab3), opus_nnue_smoke_bug.py
#     = the planted bug, opus_nnue_smoke_parity.py = tools/nnue/v2_parity.py, opus_nnue_smoke_run1t.py = the
#     one-thread wrapper, opus_nnue_smoke_mkdata.py = mkdata_material.py; every output under the scratch
#     folder, run folders named o4_* (never starting with "runs" / "smoke"; no "resid" / "kb");
#   - the PC training supervisor adopts any python process whose command line matches 'train_resid\w*\.py'
#     (F:\forge_nnue_train\tools\nnue_supervisor.ps1, Get-Train) and gpu_guard matches 'train_resid_v2.py':
#     no command line here contains either (no --guard-tag); while every run is alive and after it ends,
#     supervisor.log (read only) is checked for "adopted running job" lines, and a run is stopped at once
#     if one appears.
# Steps: 1. trainer default paths byte-identical to C4's trainer (residual, plain, 4 king buckets, mmap);
#        2. --pure on the archive's sample data (with .hce: baseline reported) and without .hce (+ --mmap-data);
#        3. --pure learnability on material-labelled synthetic data (mkdata_material.py, no .hce);
#        4. export parity on 10000 positions (C4's parity_positions.fen): v2_parity (PyTorch == C++ network)
#           and nnue_engine_eval (engine evaluation with PureNnue == network alone);
#        5. planted trainer bug (pure net exported with the residual flag) is caught.
# usage: local_cpu_checks.sh <scratch_dir> <cmake_build_dir>
set -uo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd)
# Native Windows programs get mixed paths (D:/...): MSYS does not convert arguments that contain a wildcard.
mixed() { if command -v cygpath > /dev/null; then cygpath -m "$1"; else echo "$1"; fi; }
SCR=$(mixed "$1")
BD=$(mixed "$2")
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SUP=/f/forge_nnue_train/supervisor.log
ARCH=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
DATA=$(mixed "$ARCH/5_nnue/sample_data/data32_sample/data32_sample_50k")
FENS=$(mixed "$REPO/opus_round1/C4/parity_positions.fen")
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
status=0
mkdir -p "$SCR/tools"
T=$SCR/tools
cp "$REPO/tools/nnue/train_resid_v3b.py" "$T/opus_nnue_smoke.py"
(cd "$REPO" && MSYS_NO_PATHCONV=1 git show d9a73ab3:tools/nnue/train_resid_v3b.py) > "$T/opus_nnue_smoke_c4ref.py"
cp "$REPO/tools/nnue/forge_nnue_v2.py" "$REPO/tools/nnue/qa_adam_dml.py" "$REPO/opus_round1/O4/opus_nnue_smoke_run1t.py" "$T/"
cp "$REPO/opus_round1/O4/mkdata_material.py" "$T/opus_nnue_smoke_mkdata.py"
sed 's/^import train_resid_v3b as T  # noqa: E402$/import opus_nnue_smoke as T  # noqa: E402/' "$REPO/tools/nnue/v2_parity.py" > "$T/opus_nnue_smoke_parity.py"
grep -q '^import opus_nnue_smoke as T' "$T/opus_nnue_smoke_parity.py" || { echo "parity copy: import not renamed"; exit 1; }
md5sum "$T"/*.py

sup_start=0
supervisor_check() { # label
  local new
  new=$(tail -n +"$((sup_start + 1))" "$SUP" 2>/dev/null)
  if printf '%s\n' "$new" | grep -q "adopted running job"; then
    echo "SUPERVISOR ADOPTED A JOB ($1):"
    printf '%s\n' "$new" | grep "adopted running job"
    return 1
  fi
  return 0
}
# run <name> <script> [args...]: trainer runs with --run-dir $SCR/<name>, log $SCR/<name>.log
run() {
  local name=$1 script=$2
  shift 2
  sup_start=$(wc -l < "$SUP")
  nice -n 19 "$PY" "$T/opus_nnue_smoke_run1t.py" "$T/$script" "$@" --run-dir "$SCR/$name" > "$SCR/$name.log" 2>&1 &
  local pid=$! checks=0
  echo "-- $name: started PID $pid: python opus_nnue_smoke_run1t.py $script $* --run-dir $SCR/$name"
  while kill -0 "$pid" 2> /dev/null; do
    if ! supervisor_check "$name running"; then kill "$pid"; wait "$pid"; echo "-- $name STOPPED"; return 1; fi
    checks=$((checks + 1))
    sleep 5
  done
  wait "$pid"
  local rc=$?
  supervisor_check "$name finished" || return 1
  if [ "$rc" = 3 ] && grep -q "^RAM GUARD: .*\(below the limit\|stopping\)" "$SCR/$name.log"; then
    echo "-- $name: $(grep '^RAM GUARD' "$SCR/$name.log" | tail -1)"
    echo "STOPPED: free RAM below 6 GB (user rule); no further runs"
    exit 3
  fi
  if grep -q "^train: 0 positions" "$SCR/$name.log"; then echo "-- $name: NO TRAINING DATA LOADED"; return 1; fi
  echo "-- $name: exit $rc; supervisor.log checked $checks times while running and once after: no 'adopted running job' line" \
       "($(($(wc -l < "$SUP") - sup_start)) new supervisor lines)"
  return $rc
}
outputs() { # dir: sha256 of every output except the settings dump (it holds argv and a timestamp)
  (cd "$1" && find . -type f ! -name 'settings_*' | LC_ALL=C sort | xargs sha256sum)
}
normlog() { # trainer log without timings / speeds / memory figures
  sed -E 's/ in [0-9]+s / in Ns /; s/[0-9,]+ pos\/s/N pos\/s/; s/\([0-9]+s( load)?\)/(Ns\1)/; /^MEM /d; /^RAM GUARD/d; s/ in [0-9]+s$/ in Ns/; s/run-dir .*//' "$1"
}

echo "===== 1. default paths: this branch's trainer == C4's trainer (byte-identical outputs)"
COMMON="--holdout $DATA/h000.pos --hce-dir $DATA --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6
        --seed 20261027 --batch-size 1024 --warmup-steps 10 --steps-per-epoch 40 --val-positions 8192 --log-every 1000"
for c in "a:--residual --init-check --export-v2" "b:--export-v2" "c:--residual --king-buckets 4" "d:--residual --mmap-data --final-full-val"; do
  id=${c%%:*}
  extra=${c#*:}
  # shellcheck disable=SC2086
  run "o4_id_${id}_new" opus_nnue_smoke.py --train "$DATA/t0*.pos" $COMMON $extra || status=1
  # shellcheck disable=SC2086
  run "o4_id_${id}_c4" opus_nnue_smoke_c4ref.py --train "$DATA/t0*.pos" $COMMON $extra || status=1
  if [ "$(outputs "$SCR/o4_id_${id}_new" | sha256sum)" = "$(outputs "$SCR/o4_id_${id}_c4" | sha256sum)" ] &&
     [ "$(normlog "$SCR/o4_id_${id}_new.log" | sha256sum)" = "$(normlog "$SCR/o4_id_${id}_c4.log" | sha256sum)" ] &&
     [ "$(outputs "$SCR/o4_id_${id}_new" | wc -l)" -ge 3 ]; then
    echo "IDENTICAL ($extra): $(outputs "$SCR/o4_id_${id}_new" | wc -l) output files and the normalised log"
  else
    echo "DIFFERENT ($extra)"; status=1
    diff <(outputs "$SCR/o4_id_${id}_new") <(outputs "$SCR/o4_id_${id}_c4")
    diff <(normlog "$SCR/o4_id_${id}_new.log") <(normlog "$SCR/o4_id_${id}_c4.log") | head -20
  fi
  outputs "$SCR/o4_id_${id}_new"
done

echo "===== 2. --pure on the archive's sample data"
run o4_cpu_sample opus_nnue_smoke.py --pure --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" --device cpu \
  --shape 256 --epochs 3 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 --steps-per-epoch 200 \
  --val-positions 16384 --log-every 1000 --final-full-val || status=1
grep -E "BASELINE|train:|steps/epoch|EPOCH|Saved|FINAL|Finished" "$SCR/o4_cpu_sample.log"
run o4_cpu_nohce opus_nnue_smoke.py --pure --mmap-data --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --device cpu \
  --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 10 --steps-per-epoch 40 \
  --val-positions 8192 --log-every 1000 --final-full-val || status=1
grep -E "BASELINE|train:|EPOCH|Saved|FINAL|Finished" "$SCR/o4_cpu_nohce.log"
"$PY" "$T/opus_nnue_smoke_run1t.py" "$T/opus_nnue_smoke.py" --pure --residual --train x --holdout x --device cpu \
  --run-dir "$SCR/o4_cpu_refused" > "$SCR/o4_cpu_refused.log" 2>&1
if grep -q "error: --pure trains a stand-alone net" "$SCR/o4_cpu_refused.log"; then
  echo "--pure --residual refused: $(grep -E 'error' "$SCR/o4_cpu_refused.log" | tail -1)"
else echo "--pure --residual NOT refused: $(tail -1 "$SCR/o4_cpu_refused.log")"; status=1; fi
"$PY" "$T/opus_nnue_smoke_run1t.py" "$T/opus_nnue_smoke.py" --train x --holdout x --device cpu --run-dir "$SCR/o4_cpu_refused" \
  > "$SCR/o4_cpu_refused2.log" 2>&1
if grep -q "error: --hce-dir is required" "$SCR/o4_cpu_refused2.log"; then
  echo "no --hce-dir without --pure refused: $(grep -E 'error' "$SCR/o4_cpu_refused2.log" | tail -1)"
else echo "missing --hce-dir without --pure NOT refused: $(tail -1 "$SCR/o4_cpu_refused2.log")"; status=1; fi

echo "===== 3. --pure learnability: material-labelled synthetic data (no .hce)"
MAT=$SCR/o4_material_data
mkdir -p "$MAT"
(cd "$MAT" && nice -n 19 "$PY" "$T/opus_nnue_smoke_mkdata.py" t 50000 50000 50000 50000 && \
 nice -n 19 "$PY" "$T/opus_nnue_smoke_mkdata.py" h 50000) > "$SCR/o4_material_data.log" 2>&1
cmp -s "$MAT/t000.pos" "$MAT/h000.pos" && { echo "holdout equals a training file"; status=1; }
cat "$SCR/o4_material_data.log"
run o4_cpu_material opus_nnue_smoke.py --pure --train "$MAT/t0*.pos" --holdout "$MAT/h000.pos" --device cpu --shape 256 \
  --epochs 4 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 30 --steps-per-epoch 195 \
  --val-positions 16384 --log-every 1000 || status=1
grep -E "BASELINE|train:|steps/epoch|EPOCH|Saved|Finished" "$SCR/o4_cpu_material.log"

echo "===== 4. export parity (10000 positions) and the engine's PureNnue evaluation"
for name in o4_cpu_sample o4_cpu_material; do
  NET=$(ls "$SCR/$name"/epoch00[34]-*.fnn2 | tail -1)
  echo "-- $name: $(basename "$NET")"
  nice -n 19 "$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$SCR/cpp_$name" || status=1
  sup_start=$(wc -l < "$SUP")
  nice -n 19 "$PY" "$T/opus_nnue_smoke_run1t.py" "$T/opus_nnue_smoke_parity.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$SCR/cpp_$name" \
    --json "$SCR/parity_$name.json" > "$SCR/parity_$name.log" 2>&1
  cat "$SCR/parity_$name.log"
  grep -q "^PASS" "$SCR/parity_$name.log" || status=1
  supervisor_check "parity $name" || status=1
  nice -n 19 "$BD/forge_nnue_engine_eval" "$FENS" "$SCR/engine_$name.tsv" "NNUEFile=$NET" PureNnue=1 | tee "$SCR/engine_$name.log"
  grep -q "^PASS" "$SCR/engine_$name.log" || status=1
done

echo "===== 5. planted trainer bug: the pure net exported with the residual flag"
"$PY" - "$T/opus_nnue_smoke.py" "$T/opus_nnue_smoke_bug.py" <<'PY'
import sys
s = open(sys.argv[1], encoding="utf-8").read()
old = "            if a.export_v2 or a.pure:  # O4: a pure net is used through NNUEFile + PureNnue, i.e. as a v2 file\n                export_forge_v2(model, stem, bool(a.residual))"
assert s.count(old) == 1
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(s.replace(old, old.replace("bool(a.residual))", "True)")))
PY
run o4_cpu_bug opus_nnue_smoke_bug.py --pure --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" --device cpu \
  --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 10 --steps-per-epoch 40 \
  --val-positions 8192 --log-every 1000 || status=1
NET=$(ls "$SCR/o4_cpu_bug"/epoch001-*.fnn2)
nice -n 19 "$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$SCR/cpp_o4_cpu_bug" > /dev/null
nice -n 19 "$PY" "$T/opus_nnue_smoke_run1t.py" "$T/opus_nnue_smoke_parity.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$SCR/cpp_o4_cpu_bug" \
  > "$SCR/parity_o4_cpu_bug.log" 2>&1
grep -E "^export|^PASS|^FAIL" "$SCR/parity_o4_cpu_bug.log"
grep -q "^FAIL" "$SCR/parity_o4_cpu_bug.log" && echo "planted bug caught by the parity check (export)" || { echo "planted bug NOT caught"; status=1; }
nice -n 19 "$BD/forge_nnue_engine_eval" "$FENS" "$SCR/engine_o4_cpu_bug.tsv" "NNUEFile=$NET" PureNnue=1 > "$SCR/engine_o4_cpu_bug.log"
rc=$?
cat "$SCR/engine_o4_cpu_bug.log"
[ "$rc" = 2 ] && echo "planted bug refused by the engine (exit 2)" || { echo "planted bug NOT refused by the engine (exit $rc)"; status=1; }
echo "local_cpu_checks status=$status"
exit $status
