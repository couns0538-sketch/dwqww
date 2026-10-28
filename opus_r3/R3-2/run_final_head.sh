#!/usr/bin/env bash
# R3-2 follow-up after run_matrix.sh: (1) the final-head exes (build_final_head.sh), (2) nodes + NPS of the head-3
# configurations (each against base_h3, H3DRIFT = base_h3 against the first-pass base), (3) confirmation of the two
# switch results that disagree with their own reports: 8 more ABBA pairs at d16 (appended) and a d20 block for
# FORGE_NOZERO_MOVE_BUFFERS and FORGE_NNUE_O2 (first-pass exes, results in results_d20/).
# usage: nice -n 19 bash opus_r3/R3-2/run_final_head.sh
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
WT=$(cd "$HERE/../.." && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
OUT=F:/opus_scratch/r3/R3-2/results
LOG=/f/opus_scratch/r3/R3-2/logs
H3=H3DRIFT,O2H3,LAZYSW,LAZY,O2_LAZY,LAZY_THR,PROFSW,PROF,PROF_CM_CE,INT16SW,INT16,O2_INT16,INT16_LAZY,INT16_THR
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
echo "start $(date '+%F %T') free RAM $(free_gb) GB"
nice -n 19 bash "$HERE/build_final_head.sh" "$WT" /f/opus_scratch/build/r3_R3-2 > "$LOG/build_final_head.log" 2>&1
echo "builds done $(date '+%F %T') status $? free RAM $(free_gb) GB"
nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" nodes --only "$H3" --reps 2 --out "$OUT" > "$LOG/nodes_h3.log" 2>&1
echo "nodes done $(date '+%F %T') status $?"
nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" nps --only "$H3" --runs 8 --skip-done --out "$OUT" > "$LOG/nps_h3.log" 2>&1
echo "nps done $(date '+%F %T') status $?"
nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" nps --only NOZERO,O2 --runs 8 --append --out "$OUT" > "$LOG/nps_confirm_d16.log" 2>&1
echo "confirm d16 done $(date '+%F %T') status $?"
nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" nps --only NOZERO,O2 --runs 8 --depth 20 --out F:/opus_scratch/r3/R3-2/results_d20 \
  > "$LOG/nps_confirm_d20.log" 2>&1
echo "confirm d20 done $(date '+%F %T') status $?"
for m in cycles cpu; do
  "$PY" -I -B "$HERE/r3_matrix.py" report --metric "$m" --out "$OUT" --md "$LOG/matrix_tables_$m.md" > /dev/null 2>&1
done
"$PY" -I -B "$HERE/r3_matrix.py" report --metric cycles --out F:/opus_scratch/r3/R3-2/results_d20 \
  --md "$LOG/matrix_tables_d20_cycles.md" > /dev/null 2>&1
echo "reports done $(date '+%F %T')"
