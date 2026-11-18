#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job18
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
engine=/workspace/work/sol3-job16/build_readers/forge
mode=$1
setting=$2
out=$3
fixture=$4
args=("$engine" "$out" "$mode" "$setting" "$fixture")
mkdir -p "$out"
run_code=0
{
  printf 'python3 -B %q' "$job/search18.py"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$engine" "$job"/{search18.py,ladder.py,identity.py,S14.setoption.txt} "$fixture"
  date -u +%FT%TZ
} > "$out/run.meta"
left=$((cutoff - $(date -u +%s)))
if ((left > 0)); then
  timeout --kill-after=5s "$left" python3 -B "$job/search18.py" "${args[@]}" > "$out/driver.stdout.txt" 2> "$out/driver.stderr.txt" || run_code=$?
else
  run_code=124
fi
{
  printf 'exit_code %s\n' "$run_code"
  date -u +%FT%TZ
} >> "$out/run.meta"
exit "$run_code"
