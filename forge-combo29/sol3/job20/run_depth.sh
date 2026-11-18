#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job20
net=/workspace/work/sol3-job4-net/net768.fnn3
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
phase=$1
arm=$2
engine=$3
mode=$4
depth=$5
fixture=$6
shift 6
dir="$job/$phase"
mkdir -p "$dir"
expected=$(sha256sum "$engine" | cut -d' ' -f1)
args=(python3 -B "$job/shadow_depth.py" run --build "$arm" --engine "$engine"
      --exe-sha256 "$expected" --net "$net" --fixture "$fixture" --output "$dir/$arm"
      --mode "$mode" --depth "$depth" --timeout 120 "$@")
printf '%q ' "${args[@]}" > "$dir/$arm.command.txt"
printf '\n' >> "$dir/$arm.command.txt"
run_code=0
remaining=$((cutoff - $(date -u +%s)))
if ((remaining > 0)); then
  timeout --kill-after=5s "$remaining" "${args[@]}" > "$dir/$arm.driver.stdout.txt" 2> "$dir/$arm.driver.stderr.txt" || run_code=$?
else
  run_code=124
fi
printf '%s %s %s run exit %s\n' "$(date -u +%FT%TZ)" "$phase" "$arm" "$run_code" >> "$job/stamps.txt"
git add -- "$job"
git commit -m "sol3 job 20 $phase $arm raw run"
bash /workspace/work/sol3-job3/push-checkpoint.sh
if ((run_code != 0)); then cat "$dir/$arm.driver.stderr.txt"; exit "$run_code"; fi
