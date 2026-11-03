#!/usr/bin/env bash
# opus_status.sh [--ci] [WORKTREE_GLOB] - Opus R14-B: one read-only look at a job on grok-pc (own code).
# Prints: the PC clock; per worktree (default glob o14b-*) its branch, head, ahead / behind its upstream and
# uncommitted files; with --ci the latest GitHub Actions run of each branch (needs gh + network); own running work
# (python / probe / g++ / PowerShell launchers with their priority, affinity, CPU seconds and command); who uses CPUs
# 2-3 right now; free RAM and the disks against the PC floors (C: / D: >= 50 GB, F: write-forbidden); the head of
# the crew's npt keeper STATUS (the live training line). Changes nothing.
set -u
ci=0
[ "${1:-}" = "--ci" ] && { ci=1; shift; }
glob=${1:-o14b-*}
here=$(cd "$(dirname "$0")" && pwd)
wt=/d/grok-pc-data/dwqww/.claude/worktrees
echo "== $(date '+%F %T') PC clock"
for d in $wt/$glob; do
  [ -d "$d/.git" ] || [ -f "$d/.git" ] || continue
  b=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)
  ab=$(git -C "$d" rev-list --left-right --count '@{u}...HEAD' 2>/dev/null | awk '{print "behind " $1 " ahead " $2}')
  dirty=$(git -C "$d" status --short 2>/dev/null)
  n=$(printf '%s' "$dirty" | grep -c . || true)
  echo "-- $(basename "$d"): $b $(git -C "$d" log -1 --format='%h %cd %s' --date=format:'%H:%M' | cut -c1-90)"
  echo "   ${ab:-no upstream}; uncommitted: $n $(printf '%s' "$dirty" | head -3 | awk '{print $2}' | tr '\n' ' ')"
  if [ $ci = 1 ]; then
    run=$(cd "$d" && gh run list --branch "$b" --limit 1 --json status,conclusion,name,createdAt \
      --jq '.[] | "\(.name): \(.status) \(.conclusion // "") \(.createdAt)"' 2>/dev/null)
    echo "   CI: ${run:-no runs}"
  fi
done
echo "== own work (python / probes / builds / launchers)"
powershell -NoProfile -Command "
\$pat = 'relabel2|forge_data_probe|fl_equal|fl_abba|fl_dataset|lm_det|train\.py.*o14b|g\+\+|lowrun\.ps1|probe_bench|measure_rates|bridge_check|fresh_checkout|verify_chain|build_probe|build_fastloader'
Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match \$pat -and \$_.CommandLine -notmatch 'Get-CimInstance|shell-snapshots' } | ForEach-Object {
  \$p = Get-Process -Id \$_.ProcessId -ErrorAction SilentlyContinue
  \$c = (\$_.CommandLine -replace '\s+', ' ' -replace '\"', '' -replace '[A-Za-z]:[/\\\\]grok-pc-data[/\\\\]dwqww[/\\\\]\.claude[/\\\\]worktrees[/\\\\]', '<wt>/' -replace '\S*python\.exe', 'py')
  if (\$p) { '  {0,-6} {1,-18} {2,-11} aff 0x{3:X} cpu {4,7:N0}s  {5}' -f \$_.ProcessId, \$_.Name, \$p.PriorityClass, [int64]\$p.ProcessorAffinity, \$p.CPU, \$c.Substring(0, [Math]::Min(120, \$c.Length)) }
}" 2>/dev/null
echo "== processes allowed on CPUs 2-3 that used CPU in the last 3 s (cores = their use on any CPU)"
powershell -NoProfile -File "$(cygpath -w "$here/cpu_users.ps1")" -Mask 0xC -Seconds 3 2>/dev/null | tail -n +2 | head -6
echo "== memory and disks (floors: C: / D: >= 50 GB; F: write-forbidden)"
powershell -NoProfile -Command "
\$os = Get-CimInstance Win32_OperatingSystem
'  RAM free {0:N1} of {1:N1} GB' -f (\$os.FreePhysicalMemory / 1MB), (\$os.TotalVisibleMemorySize / 1MB)
foreach (\$d in 'C', 'D', 'F') { \$v = Get-PSDrive \$d -ErrorAction SilentlyContinue; if (\$v) { '  {0}: {1,6:N1} GB free' -f \$d, (\$v.Free / 1GB) } }" 2>/dev/null
keeper=/c/Users/Administrator/grok-pc/forge_push/npt_keeper/STATUS.md
if [ -f "$keeper" ]; then
  echo "== npt keeper STATUS (crew, read-only)"
  grep -m 4 "Training runs live\|npt trainer running\|Next pending\|GPU" "$keeper" | cut -c1-150 | sed 's/^/  /'
fi
