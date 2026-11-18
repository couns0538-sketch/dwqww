#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job22
build=/workspace/work/sol3-job22-build/build
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 22 prediction'
rg -Fq 'Step 2 sanitizer control diagnostic gate exit 0' "$job/stamps.txt"
for engine in AU-r15d AU-kF; do
  for part in au-d9 au-games; do
    if (($(date -u +%s) >= cutoff)); then exit 0; fi
    name=$engine-${part#au-}
    code=0
    for attempt in 1 2 3; do
      label=$name
      if ((attempt > 1)); then label="$name-startup-retry-$attempt"; fi
      bash "$job/run_case.sh" "$build/$engine/forge" "$part" "$label" clean || code=$?
      out="$job/clean/$label"
      if [[ ! -f "$out/engine.stderr.txt" ]] || ! rg -q '^AddressSanitizer:DEADLYSIGNAL' "$out/engine.stderr.txt" ||          rg -q '^uciok$' "$out/engine.stdout.txt"; then
        break
      fi
    done
  done
done
if [[ "$(cat "$job/T-startup/status.txt")" == available ]]; then
  launcher=()
  if [[ "$(cat "$job/T-startup/launcher.txt")" == setarch_R ]]; then launcher=(--setarch-r); fi
  for engine in T-r15d T-kF; do
    if (($(date -u +%s) >= cutoff)); then exit 0; fi
    code=0
    bash "$job/run_case.sh" "$build/$engine/forge" t-clean "$engine" clean "${launcher[@]}" || code=$?
    out="$job/clean/$engine"
    if [[ -f "$out/engine.stderr.txt" ]] && rg -q '^FATAL: ThreadSanitizer:' "$out/engine.stderr.txt" &&        ! rg -q '^uciok$' "$out/engine.stdout.txt" && [[ ! -f "$job/T-startup/setarch_R.exit.txt" ]] &&        ! compgen -G "$job/controls/*setarch-R" > /dev/null && ! compgen -G "$job/clean/*setarch-R" > /dev/null; then
      bash "$job/run_case.sh" "$build/$engine/forge" t-clean "$engine-setarch-R" clean --setarch-r || code=$?
    fi
  done
fi
