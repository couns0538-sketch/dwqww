#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job18
prior=forge-combo29/sol3/job17
test "$(cat "$job/stage0/gate.txt")" = 'exit_code 0'
for arm in A B; do
  out="$job/K1/$arm"
  run_code=0
  compare_code=125
  bash "$job/run_one.sh" ladder "$arm" "$out" "$job/references/P.fen.txt" || run_code=$?
  if ((run_code == 0)); then
    compare_code=0
    python3 -B "$job/compare.py" "$prior/K1/$arm/rows.tsv" "$out/rows.tsv" > "$out/comparison.txt" 2>&1 || compare_code=$?
  fi
  printf '%s K1 %s run exit %s comparison exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$run_code" "$compare_code" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 18 K1 $arm retain ladder and gate"
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
