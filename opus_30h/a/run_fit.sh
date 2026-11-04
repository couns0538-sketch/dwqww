#!/usr/bin/env bash
# run_fit.sh <run dir> <cpu mask> [o30_fit.py train arguments ...] - resumable launcher of the CPU fine-tune.
# A new run when <run dir>/last.pt does not exist (all arguments are passed), otherwise `--resume` (only --until /
# --positions are taken from the arguments; the rest comes from the run's own checkpoint). Before starting: D: >= 51 GB
# and C: >= 30 GB free, free RAM >= 8 GB, the NNUE supervisor's "adopted running job" count is recorded (and checked
# again after 60 s: a new adoption line = stop and report). The trainer runs at Idle on <cpu mask> (lowrun.ps1, children
# inherit). Logs: D:\o30\logs\fit_<run name>_<YYYYmmdd_HHMMSS>.{out,err} (new files per session, never overwritten).
set -uo pipefail
run="$1"; mask="$2"; shift 2
A=$(cd "$(dirname "$0")" && pwd); T="$A/../tools"
name=$(basename "$run")
dfree=$(df -BG /d | awk 'NR==2 {gsub("G","",$4); print $4}'); cfree=$(df -BG /c | awk 'NR==2 {gsub("G","",$4); print $4}')
if [ "${dfree:-0}" -lt 51 ] || [ "${cfree:-0}" -lt 30 ]; then echo "STOP: D: ${dfree} GB / C: ${cfree} GB below the floor"; exit 76; fi
ram=$(powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)")
awk -v r="$ram" 'BEGIN { exit !(r >= 8) }' || { echo "STOP: free RAM $ram GB < 8"; exit 77; }
adopt0=$(grep -c "adopted running job" /f/forge_nnue_train/supervisor.log)
if [ -e "$run/last.pt" ]; then
  keep=(); while [ $# -gt 0 ]; do case "$1" in --until|--positions) keep+=("$1" "$2"); shift 2;; *) shift;; esac; done
  args=(train --out "$(cygpath -w "$run")" --resume "${keep[@]}")
else
  args=(train --out "$(cygpath -w "$run")" "$@")
fi
stamp=$(date +%Y%m%d_%H%M%S)
line="-I -B $(cygpath -w "$A/o30_fit.py")"
for x in "${args[@]}"; do case "$x" in *" "*) line="$line \"$x\"";; *) line="$line $x";; esac; done
echo "$(date '+%F %T') run_fit: D: ${dfree} GB C: ${cfree} GB RAM ${ram} GB adopted ${adopt0}; python $line"
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/lowrun.ps1")" -Mask "$mask" -Priority Idle \
  -Exe 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe' -ArgLine "$line" \
  -Out "D:\\o30\\logs\\fit_${name}_${stamp}.out" -Err "D:\\o30\\logs\\fit_${name}_${stamp}.err" &
pid=$!
sleep 60
adopt1=$(grep -c "adopted running job" /f/forge_nnue_train/supervisor.log)
[ "$adopt1" = "$adopt0" ] || echo "WARNING: supervisor adoption count changed $adopt0 -> $adopt1: stop the run and report"
wait $pid
rc=$?
echo "$(date '+%F %T') run_fit: exit $rc"
exit $rc
