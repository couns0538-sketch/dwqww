#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job22
build=/workspace/work/sol3-job22-build/build
net=/workspace/work/sol3-job4-net/net768.fnn3
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
set -a
source "$job/sanitizer.env.txt"
set +a
if (($# == 0)); then set -- AU-r15d AU-kF; fi
for arm in "$@"; do
  [[ "$arm" == AU-r15d || "$arm" == AU-kF ]]
  for depth in 11 13; do
    out="$job/known/$arm/bench_$depth"
    mkdir -p "$(dirname "$out")"
    remaining=$((cutoff - $(date -u +%s)))
    if ((remaining <= 0)); then exit 124; fi
    code=0
    timeout --kill-after=3s "$remaining" python3 -B "$job/au_pins.py" "$build/$arm/forge" "$net" "$depth" "$out" \
      > "$out.driver.stdout.txt" 2> "$out.driver.stderr.txt" || code=$?
    printf '%s Step 1 %s bench %s known-answer runner exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$depth" "$code" >> "$job/stamps.txt"
    git add -- "$job"
    git commit -m "sol3 job 22 step 1 retain $arm bench $depth"
    bash /workspace/work/sol3-job3/push-checkpoint.sh
    if [[ -f "$out/summary.json" ]]; then cat "$out/summary.json"; else cat "$out.driver.stderr.txt"; fi
  done
done
