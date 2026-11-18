#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job15
work=/workspace/work/sol3-job15
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
engine=$1
out=$2
fixture=$3
shift 3
args=("$engine" "$out" "$fixture" "$@")
mkdir -p "$out"
status=0
{
  printf 'PYTHONPATH=%q python3 -B %q' "$work" "$job/fixed_depth.py"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$engine" "$job/fixed_depth.py" "$work/identity.py" "$fixture"
  date -u +%FT%TZ
} > "$out/run.meta"
left=$((cutoff - $(date -u +%s)))
if ((left > 0)); then
  PYTHONPATH="$work" timeout --kill-after=5s "$left" python3 -B "$job/fixed_depth.py" "${args[@]}" > "$out/driver.stdout.txt" 2> "$out/driver.stderr.txt" || status=$?
else
  status=124
fi
{
  printf 'exit_code %s\n' "$status"
  date -u +%FT%TZ
} >> "$out/run.meta"
exit "$status"
