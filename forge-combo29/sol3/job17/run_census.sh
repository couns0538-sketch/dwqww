#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job17
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
last_start=$(($(date -u -d "$claim" +%s) + 2700))
test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 17 prediction'
test "$(cat "$job/stage0/gate.txt")" = 'exit_code 0'
for known in A B C D E F; do
  rg -Fxq 'matching rows 20/20' "$job/K1/$known/comparison.txt"
done
test -s "$job/K1/G/rows.tsv"
for arm in A B D C E G F; do
  if (($(date -u +%s) >= last_start)); then
    printf 'Minute 45 crossed before starting setting %s.\n' "$arm"
    break
  fi
  run_code=0
  out="$job/census/$arm"
  bash "$job/run_one.sh" census "$arm" "$out" "$job/positions.txt" || run_code=$?
  printf '%s Census %s run exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$run_code" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 17 census $arm retain depth-16 searches"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if ((run_code != 0)); then
    cat "$out/driver.stderr.txt"
    exit "$run_code"
  fi
  wc -l "$out/rows.tsv"
done
