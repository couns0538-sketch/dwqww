#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job16
engine=/workspace/work/sol3-job16/build_split/forge
for arm in both_on both_off quiet_only correction_only; do
  case $arm in
    both_on) quiet=2; correction=2 ;;
    both_off) quiet=0; correction=0 ;;
    quiet_only) quiet=2; correction=0 ;;
    correction_only) quiet=0; correction=2 ;;
  esac
  out="$job/part1/$arm"
  legacy=()
  if [[ $arm == both_off ]]; then
    legacy=(--option HistRework=2)
  fi
  status=0
  bash "$job/run_one.sh" "$engine" "$out" --profile S14 "${legacy[@]}" \
    --option "HistReworkQuiet=$quiet" --option "HistReworkCorrection=$correction" || status=$?
  comparison=125
  if ((status == 0)); then
    comparison=0
    python3 -B "$job/compare.py" "$job/references/$arm.tsv" "$out/rows.tsv" > "$out/comparison.txt" 2>&1 || comparison=$?
  fi
  printf '%s Part 1 %s engine exit %s reference comparison exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$status" "$comparison" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 16 step 1 retain $arm ladder and comparison"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  cat "$out/run.meta"
  if [[ -f "$out/comparison.txt" ]]; then
    cat "$out/comparison.txt"
  else
    cat "$out/driver.stderr.txt"
    exit "$status"
  fi
done
