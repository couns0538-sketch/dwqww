#!/usr/bin/env bash
set -euo pipefail
engine=$1
out=$2
limit=$3
cell=$4
work=/workspace/work/sol3-job12
net=/workspace/work/sol3-job4-net/net768.fnn3
fixture=forge-combo29/sol3/job3/positions.txt
cutoff=$(date -u -d 2026-11-18T14:02:20Z +%s)
remaining=$((cutoff - $(date -u +%s)))
args=("$engine" "$fixture" "$out" 11 "$cell" --nodes "$limit")
if [ "$cell" = N2 ]; then args+=(--net "$net"); fi
mkdir "$out"
status=0
{
  printf 'python3 -B %q' "$work/identity.py"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$engine" "$work/identity.py" "$fixture"
  if [ "$cell" = N2 ]; then sha256sum "$net"; fi
  date -u +%FT%TZ
} > "$out/run.meta"
if ((remaining > 0)); then
  timeout --kill-after=5s "$remaining" python3 -B "$work/identity.py" "${args[@]}" > "$out/driver.stdout.txt" 2> "$out/driver.stderr.txt" || status=$?
else
  status=124
fi
printf 'exit_code %s\n' "$status" >> "$out/run.meta"
exit "$status"
