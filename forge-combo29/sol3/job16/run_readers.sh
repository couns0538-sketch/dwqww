#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job16
engine=/workspace/work/sol3-job16/build_readers/forge
test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 16 prediction'
for profile in S14 PC20; do
  base=()
  if [[ $profile == S14 ]]; then
    base=(--option HistReworkQuiet=2 --option HistReworkCorrection=0)
  fi
  for index in {1..6}; do
    case $index in
      1) switches=(1 0 0) ;;
      2) switches=(0 1 0) ;;
      3) switches=(0 0 1) ;;
      4) switches=(0 1 1) ;;
      5) switches=(1 0 1) ;;
      6) switches=(1 1 0) ;;
    esac
    out="$job/part3/$profile/L$index"
    status=0
    bash "$job/run_one.sh" "$engine" "$out" --profile "$profile" "${base[@]}" \
      --option "QuietReadPlainR1=${switches[0]}" --option "QuietReadPlainR2=${switches[1]}" \
      --option "QuietReadPlainR3=${switches[2]}" || status=$?
    printf '%s Part 3 %s L%s switches %s engine exit %s\n' "$(date -u +%FT%TZ)" "$profile" "$index" "${switches[*]}" "$status" >> "$job/stamps.txt"
    git add -- "$job"
    git commit -m "sol3 job 16 step 3 retain $profile L$index ladder"
    bash /workspace/work/sol3-job3/push-checkpoint.sh
    if ((status != 0)); then
      cat "$out/driver.stderr.txt"
      exit "$status"
    fi
    tail -1 "$out/rows.tsv" | cut -f1-6
  done
done
