#!/usr/bin/env bash
# R3-2: the full matrix pass. Nodes (bench d11/13/16, 2 fresh processes per T1 configuration), then NPS (ABBA vs
# the OFF exe, RUNS fresh processes per side, bench d16 / T2 go depth 16), then the report tables.
# usage: nice -n 19 bash opus_r3/R3-2/run_matrix.sh [RUNS] [extra r3_matrix.py args for nodes/nps, e.g. --only X,Y]
set -uo pipefail
RUNS=${1:-8}; shift || true
HERE=$(cd "$(dirname "$0")" && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
OUT=F:/opus_scratch/r3/R3-2/results
LOG=/f/opus_scratch/r3/R3-2/logs
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
echo "start $(date '+%F %T') free RAM $(free_gb) GB runs/side $RUNS args: $*"
nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" nodes --reps 2 --out "$OUT" "$@" > "$LOG/nodes.log" 2>&1
echo "nodes done $(date '+%F %T') status $? free RAM $(free_gb) GB"
nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" nps --runs "$RUNS" --depth 16 --depth-t2 16 --skip-done --out "$OUT" "$@" \
  > "$LOG/nps.log" 2>&1
echo "nps done $(date '+%F %T') status $? free RAM $(free_gb) GB"
for m in cpu cycles; do
  nice -n 19 "$PY" -I -B "$HERE/r3_matrix.py" report --metric "$m" --out "$OUT" --md "$LOG/report_$m.md" > /dev/null 2>&1
done
echo "report done $(date '+%F %T')"
