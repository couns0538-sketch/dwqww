#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job16
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
engine=$1
out=$2
shift 2
fixture="$job/references/P.fen.txt"
args=("$engine" "$out" "$fixture" "$@")
mkdir -p "$out"
status=0
{
  printf 'python3 -B %q' "$job/ladder.py"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$engine" "$job/ladder.py" "$job/identity.py" "$fixture" "$job/S14.setoption.txt"
  date -u +%FT%TZ
} > "$out/run.meta"
left=$((cutoff - $(date -u +%s)))
if ((left > 0)); then
  timeout --kill-after=5s "$left" python3 -B "$job/ladder.py" "${args[@]}" > "$out/driver.stdout.txt" 2> "$out/driver.stderr.txt" || status=$?
else
  status=124
fi
{
  printf 'exit_code %s\n' "$status"
  date -u +%FT%TZ
} >> "$out/run.meta"
exit "$status"
