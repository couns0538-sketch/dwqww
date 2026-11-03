#!/usr/bin/env bash
# trainer_watch.sh OUT.tsv UNTIL_EPOCH - Opus R14-B (read-only): every 300 s, the live npt trainer's CPU share on its own
# mask, the busiest other processes on that mask, and the GPU utilisation of the same 5 minutes (keeper's HWiNFO log).
# Never touches a process (Get-Process / CIM reads only); writes only OUT.tsv. Stops at UNTIL_EPOCH (date +%s).
set -u
out=${1:?out}; until=${2:?until epoch}
[ -e "$out" ] && { echo "refusing existing $out"; exit 2; }
# final bug hunt (04:15): a non-number or past UNTIL_EPOCH used to write the header only and exit 0 - a watcher that
# silently records nothing
case $until in '' | *[!0-9]*) echo "UNTIL_EPOCH must be seconds since 1970 (date -d 'YYYY-MM-DD HH:MM' +%s), not '$until'" >&2; exit 2 ;; esac
[ "$until" -gt "$(date +%s)" ] || { echo "UNTIL_EPOCH $until is not in the future: nothing to watch" >&2; exit 2; }
T=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-status/opus_r14b/tools
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
printf 'time\ttrainer_pid\tmask\tpriority\ttrainer_cores\tothers_on_mask_cores\ttop_other\tgpu_util_mean_5min\tgpu_util_p50\n' > "$out"
while [ "$(date +%s)" -lt "$until" ]; do
  row=$(powershell -NoProfile -Command "
    \$t = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'guard_tag=train_resid_v2' -and \$_.CommandLine -notmatch 'Scripts\\\\python.exe' } | Select-Object -First 1
    if (-not \$t) { 'none'; exit }
    \$p = Get-Process -Id \$t.ProcessId -ErrorAction SilentlyContinue
    if (-not \$p) { 'none'; exit }
    \$m = [int64]\$p.ProcessorAffinity
    \$before = @{}; foreach (\$q in Get-Process) { try { if (([int64]\$q.ProcessorAffinity -band \$m) -ne 0) { \$before[\$q.Id] = \$q.TotalProcessorTime.TotalSeconds } } catch {} }
    \$w0 = Get-Date; Start-Sleep -Seconds 10; \$el = ((Get-Date) - \$w0).TotalSeconds
    \$tc = 0.0; \$oc = 0.0; \$top = ''; \$topc = 0.0
    foreach (\$q in Get-Process) { try { if (\$before.ContainsKey(\$q.Id)) { \$d = (\$q.TotalProcessorTime.TotalSeconds - \$before[\$q.Id]) / \$el
          if (\$q.Id -eq \$p.Id) { \$tc = \$d } elseif (\$d -gt 0.05) { \$oc += \$d; if (\$d -gt \$topc) { \$topc = \$d; \$top = '{0}:{1}:{2}' -f \$q.ProcessName, \$q.Id, \$q.PriorityClass } } } } catch {} }
    '{0}|0x{1:X}|{2}|{3:N2}|{4:N2}|{5}' -f \$p.Id, \$m, \$p.PriorityClass, \$tc, \$oc, \$top" 2>/dev/null | tr -d '\r' | tr '|' '\t')
  gpu=$("$PY" -I -B "$T/gpu_util_stats.py" --hours 0.0834 2>/dev/null | grep "GPU Utilization" | sed -E 's/.*mean ([0-9.]+), p10 [0-9.]+, p50 ([0-9.]+).*/\1\t\2/')
  printf '%s\t%s\t%s\n' "$(date '+%F %T')" "${row:-none}" "${gpu:-na	na}" >> "$out"
  sleep 290
done
