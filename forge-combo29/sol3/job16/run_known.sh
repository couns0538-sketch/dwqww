#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job16
engine=/workspace/work/sol3-job16/build_readers/forge
for arm in S14_all_plain PC20_all_zero; do
  out="$job/part2/$arm"
  if [[ $arm == S14_all_plain ]]; then
    profile=S14
    reference="$job/part1/both_off/rows.tsv"
    overrides=(--option HistReworkQuiet=2 --option HistReworkCorrection=0 --option QuietReadPlainR1=1 --option QuietReadPlainR2=1 --option QuietReadPlainR3=1)
  else
    profile=PC20
    reference="$job/references/PC20_A1.tsv"
    overrides=(--option QuietReadPlainR1=0 --option QuietReadPlainR2=0 --option QuietReadPlainR3=0)
  fi
  status=0
  bash "$job/run_one.sh" "$engine" "$out" --profile "$profile" "${overrides[@]}" || status=$?
  comparison=125
  if ((status == 0)); then
    comparison=0
    python3 -B "$job/compare.py" "$reference" "$out/rows.tsv" > "$out/comparison.txt" 2>&1 || comparison=$?
  fi
  printf '%s Part 2 %s engine exit %s reference comparison exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$status" "$comparison" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 16 step 2 retain $arm ladder and comparison"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if [[ -f "$out/comparison.txt" ]]; then
    cat "$out/comparison.txt"
  else
    cat "$out/driver.stderr.txt"
  fi
  if [[ $arm == S14_all_plain && $comparison != 0 ]]; then
    exit "$comparison"
  fi
done
