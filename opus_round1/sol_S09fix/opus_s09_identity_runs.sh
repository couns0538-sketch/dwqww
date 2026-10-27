#!/usr/bin/env bash
# S09-1 (training path): run the CURRENT v3b trainer and the S09 v2 trainer (renamed copies only) on the same tiny
# data32 split with identical arguments, then compare every epoch artifact byte for byte. CPU only, one thread,
# Idle priority, scratch only; output folders never start with runs_ / smoke_kb; supervisor.log is checked for a
# new "adopted running job" line after every run. Nothing is adopted; no 8-head training.
# usage: opus_s09_identity_runs.sh <scratch_dir> <job_dir>
set -euo pipefail
S=$1; J=$2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
export TMP="$(cygpath -w "$S/tmp")" TEMP="$(cygpath -w "$S/tmp")"
SUP=/f/forge_nnue_train/supervisor.log
adopt0=$(grep -c "adopted running job" "$SUP" || true)
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
check_sup() {
  local n; n=$(grep -c "adopted running job" "$SUP" || true)
  echo "supervisor.log adopted-running-job lines: $n (before: $adopt0)"
  if [ "$n" != "$adopt0" ]; then echo "NEW ADOPTION LINE - stopping"; exit 3; fi
}
D="$S/inputs/split32"
DATA="--train $(cygpath -w "$D/s32train.pos") --holdout $(cygpath -w "$D/s32hold.pos") --hce-dir $(cygpath -w "$D") --device cpu"
F006TINY="--shape 256 --residual --init-check --final-full-val --log-every 1000000 --epochs 2 --batch-size 1024 --lr 7.07e-4 --blend-end 0.6 --seed 25 --warmup-steps 300 --val-positions 0"
run() {  # name trainer-copy extra-args...
  local name=$1 tr=$2; shift 2
  local fr; fr=$(free_gb); echo "== $name ($(date -u +%FT%TZ)), free RAM ${fr} GB"
  awk -v f="$fr" 'BEGIN{exit !(f>=6)}' || { echo "free RAM < 6 GB, stop"; exit 4; }
  local rc=0
  ( cd "$S" && nice -n 19 "$PY" -I -B "$tr" $DATA "$@" --run-dir "$(cygpath -w "$S/$name")" ) > "$S/$name.log" 2> "$S/$name.err" || rc=$?
  echo "rc=$rc $(grep -E '^(EPOCH|FINAL|Finished|INIT)' "$S/$name.log" | tr '\n' '|')"
  check_sup
}
run s09_id_A_current_f006tiny "$S/opus_nnue_smoke_s09_current.py" $F006TINY
run s09_id_B_v2_f006tiny      "$S/opus_nnue_smoke_s09_v2.py"      $F006TINY
run s09_id_C_v2_f006tiny_b1   "$S/opus_nnue_smoke_s09_v2.py"      $F006TINY --buckets 1
run s09_id_D_current_defaults "$S/opus_nnue_smoke_s09_current.py" --log-every 1000000
run s09_id_E_v2_defaults      "$S/opus_nnue_smoke_s09_v2.py"      --log-every 1000000
C="$J/forge_sol_S09_export_identity_v2.py"
for pair in "A_current_f006tiny B_v2_f006tiny" "A_current_f006tiny C_v2_f006tiny_b1" "D_current_defaults E_v2_defaults"; do
  set -- $pair
  echo "== compare $1 vs $2"
  nice -n 19 "$PY" -I -B "$C" compare-runs "$S/s09_id_$1" "$S/s09_id_$2" --json "$S/s09_id_compare_${1%%_*}_${2%%_*}.json" || echo "COMPARE FAILED"
done
check_sup
