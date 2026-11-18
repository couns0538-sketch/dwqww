#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job17
prior=forge-combo29/sol3/job16
test "$(cat "$job/stage0/gate.txt")" = 'exit_code 0'
for arm in A B C D E F G; do
  out="$job/K1/$arm"
  run_code=0
  compare_code=125
  bash "$job/run_one.sh" ladder "$arm" "$out" "$job/references/P.fen.txt" || run_code=$?
  case $arm in
    A) ref="$job/references/follow_off.tsv" ;;
    B) ref="$prior/part1/quiet_only/rows.tsv" ;;
    C) ref="$prior/part3/S14/L1/rows.tsv" ;;
    D) ref="$prior/part3/S14/L3/rows.tsv" ;;
    E) ref="$prior/part2/PC20_all_zero/rows.tsv" ;;
    F) ref="$prior/part3/PC20/L3/rows.tsv" ;;
    G) ref='' ;;
  esac
  if ((run_code == 0)) && [[ -n "$ref" ]]; then
    compare_code=0
    python3 -B "$job/compare.py" "$ref" "$out/rows.tsv" > "$out/comparison.txt" 2>&1 || compare_code=$?
  elif ((run_code == 0)); then
    compare_code=0
    printf 'New ladder, no reference.\n' > "$out/comparison.txt"
  fi
  printf '%s K1 %s run exit %s comparison exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$run_code" "$compare_code" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 17 K1 $arm retain ladder and gate"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if ((run_code != 0)); then
    cat "$out/driver.stderr.txt"
    exit "$run_code"
  fi
  cat "$out/comparison.txt"
  if ((compare_code != 0)); then
    exit "$compare_code"
  fi
done
