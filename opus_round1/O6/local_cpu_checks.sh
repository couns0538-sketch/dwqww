#!/usr/bin/env bash
# O6 local CPU checks on the shared Windows PC (trainer --threats + export parity), under the user's NNUE rules:
#   - CPU torch from the read-only venv, one thread (opus_nnue_smoke_run1t.py), nice 19, free-RAM guard 6 GB;
#   - every Python script that runs is a renamed copy called opus_nnue_smoke*.py: opus_nnue_smoke.py = this branch's
#     tools/nnue/train_resid_v3b.py, opus_nnue_smoke_c4ref.py = C4's (d9a73ab3), opus_nnue_smoke_bug.py = the planted
#     bug, opus_nnue_smoke_parity.py = tools/nnue/v2_parity.py, opus_nnue_smoke_run1t.py = the one-thread wrapper;
#     every output under the scratch folder, run folders named o6_* (never starting with "runs" / "smoke");
#   - the PC training supervisor adopts python processes whose command line matches 'train_resid\w*\.py': no command
#     line here contains it (no --guard-tag); supervisor.log (read only) is checked while every run is alive and after
#     it ends, and a run is stopped at once if an "adopted running job" line appears.
# Steps: 1. trainer default paths byte-identical to C4's trainer (residual, plain, 4 king buckets, mmap);
#        2. --threats training (1 bucket, residual) and --threats --king-buckets 4 (mirrored) on the archive's sample data;
#        3. export parity on 10000 positions (C4's parity_positions.fen) for both nets;
#        4. planted trainer bug (pawn attack directions swapped in the trainer's threat pairs) is caught.
# usage: local_cpu_checks.sh <scratch_dir> <cmake_build_dir>
set -uo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd)
mixed() { if command -v cygpath > /dev/null; then cygpath -m "$1"; else echo "$1"; fi; }
SCR=$(mixed "$1")
BD=$(mixed "$2")
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SUP=/f/forge_nnue_train/supervisor.log
ARCH=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
DATA=$(mixed "$ARCH/5_nnue/sample_data/data32_sample/data32_sample_50k")
FENS=$(mixed "$REPO/opus_round1/C4/parity_positions.fen")
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
status=0
mkdir -p "$SCR/tools"
T=$SCR/tools
cp "$REPO/tools/nnue/train_resid_v3b.py" "$T/opus_nnue_smoke.py"
(cd "$REPO" && MSYS_NO_PATHCONV=1 git show d9a73ab3:tools/nnue/train_resid_v3b.py) > "$T/opus_nnue_smoke_c4ref.py"
cp "$REPO/tools/nnue/forge_nnue_v2.py" "$REPO/tools/nnue/qa_adam_dml.py" "$REPO/opus_round1/O6/opus_nnue_smoke_run1t.py" "$T/"
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
outputs() { (cd "$1" && find . -type f ! -name 'settings_*' | LC_ALL=C sort | xargs sha256sum); }
normlog() { sed -E 's/ in [0-9]+s / in Ns /; s/[0-9,]+ pos\/s/N pos\/s/; s/\([0-9]+s( load)?\)/(Ns\1)/; /^MEM /d; /^RAM GUARD/d; s/ in [0-9]+s$/ in Ns/' "$1"; }
parity() { # name net
  local name=$1 net=$2
  nice -n 19 "$BD/forge_nnue_v2_tool" eval "$net" "$FENS" "$SCR/cpp_$name" || status=1
  sup_start=$(wc -l < "$SUP")
  nice -n 19 "$PY" "$T/opus_nnue_smoke_run1t.py" "$T/opus_nnue_smoke_parity.py" "${net%.fnn2}.pt" "$net" "$FENS" "$SCR/cpp_$name" \
    --json "$SCR/parity_$name.json" > "$SCR/parity_$name.log" 2>&1
  supervisor_check "parity $name" || status=1
}

echo "===== 1. default paths: this branch's trainer == C4's trainer (byte-identical outputs)"
COMMON="--holdout $DATA/h000.pos --hce-dir $DATA --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6
        --seed 20261027 --batch-size 1024 --warmup-steps 10 --steps-per-epoch 40 --val-positions 8192 --log-every 1000"
for c in "a:--residual --init-check --export-v2" "b:--export-v2" "c:--residual --king-buckets 4" "d:--residual --mmap-data --final-full-val"; do
  id=${c%%:*}
  extra=${c#*:}
  # shellcheck disable=SC2086
  run "o6_id_${id}_new" opus_nnue_smoke.py --train "$DATA/t0*.pos" $COMMON $extra || status=1
  # shellcheck disable=SC2086
  run "o6_id_${id}_c4" opus_nnue_smoke_c4ref.py --train "$DATA/t0*.pos" $COMMON $extra || status=1
  if [ "$(outputs "$SCR/o6_id_${id}_new" | sha256sum)" = "$(outputs "$SCR/o6_id_${id}_c4" | sha256sum)" ] &&
     [ "$(normlog "$SCR/o6_id_${id}_new.log" | sha256sum)" = "$(normlog "$SCR/o6_id_${id}_c4.log" | sha256sum)" ] &&
     [ "$(outputs "$SCR/o6_id_${id}_new" | wc -l)" -ge 3 ]; then
    echo "IDENTICAL ($extra): $(outputs "$SCR/o6_id_${id}_new" | wc -l) output files and the normalised log"
  else
    echo "DIFFERENT ($extra)"; status=1
  fi
done

echo "===== 2. --threats training on the archive's sample data (CPU, one thread)"
run o6_cpu_threats opus_nnue_smoke.py --threats --residual --init-check --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" \
  --hce-dir "$DATA" --device cpu --shape 256 --epochs 2 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 \
  --warmup-steps 20 --steps-per-epoch 80 --val-positions 8192 --log-every 1000 || status=1
grep -E "threat inputs|INIT|train:|steps/epoch|EPOCH|Saved|Finished" "$SCR/o6_cpu_threats.log"
run o6_cpu_threats_kb4 opus_nnue_smoke.py --threats --king-buckets 4 --residual --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" \
  --hce-dir "$DATA" --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 \
  --warmup-steps 10 --steps-per-epoch 40 --val-positions 8192 --log-every 1000 || status=1
grep -E "threat inputs|king buckets|train:|EPOCH|Saved|Finished" "$SCR/o6_cpu_threats_kb4.log"

echo "===== 3. export parity on 10000 positions"
for name in o6_cpu_threats o6_cpu_threats_kb4; do
  NET=$(ls "$SCR/$name"/epoch00*.fnn2 | tail -1)
  echo "-- $name: $(basename "$NET")"
  parity "$name" "$NET"
  cat "$SCR/parity_$name.log"
  grep -q "^PASS" "$SCR/parity_$name.log" || status=1
done

echo "===== 4. planted trainer bug: pawn attack directions swapped in the trainer's threat pairs"
"$PY" - "$T/opus_nnue_smoke.py" "$T/opus_nnue_smoke_bug.py" <<'PY'
import sys
s = open(sys.argv[1], encoding="utf-8").read()
old = "((kd == 2) & (a_l == 1)) |"
assert s.count(old) == 1
s = s.replace(old, "((kd == 2) & (a_l == 7)) |").replace("((kd == 3) & (a_l == 7)))", "((kd == 3) & (a_l == 1)))")
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(s)
PY
# The PyTorch side of the parity must use the buggy trainer's feature function (a parity copy importing it).
sed 's/^import train_resid_v3b as T  # noqa: E402$/import opus_nnue_smoke_bug as T  # noqa: E402/' "$REPO/tools/nnue/v2_parity.py" > "$T/opus_nnue_smoke_parity_bug.py"
run o6_cpu_bug opus_nnue_smoke_bug.py --threats --residual --train "$DATA/t0*.pos" --holdout "$DATA/h000.pos" --hce-dir "$DATA" \
  --device cpu --shape 256 --epochs 1 --lr 2e-3 --blend-end 0.6 --seed 20261027 --batch-size 1024 --warmup-steps 10 \
  --steps-per-epoch 20 --val-positions 4096 --log-every 1000 || status=1
NET=$(ls "$SCR/o6_cpu_bug"/epoch001-*.fnn2)
nice -n 19 "$BD/forge_nnue_v2_tool" eval "$NET" "$FENS" "$SCR/cpp_o6_cpu_bug" || status=1
nice -n 19 "$PY" "$T/opus_nnue_smoke_run1t.py" "$T/opus_nnue_smoke_parity_bug.py" "${NET%.fnn2}.pt" "$NET" "$FENS" "$SCR/cpp_o6_cpu_bug" \
  > "$SCR/parity_o6_cpu_bug.log" 2>&1
grep -E "^export|^acc|^output|^PASS|^FAIL" "$SCR/parity_o6_cpu_bug.log"
grep -q "^FAIL" "$SCR/parity_o6_cpu_bug.log" && echo "planted bug caught by the parity check" || { echo "planted bug NOT caught"; status=1; }
echo "local_cpu_checks status=$status"
exit $status
