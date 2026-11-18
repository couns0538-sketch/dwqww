#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job22
build=/workspace/work/sol3-job22-build/build/T-r15d/forge
out="$job/T-startup"
mkdir -p "$out"
printf 'uci\nquit\n' > "$out/commands.txt"
set -a
source "$job/sanitizer.env.txt"
set +a
probe() {
  local mode=$1
  shift
  local code=0
  printf '%q ' "$@" > "$out/$mode.invocation.txt"
  printf '\n' >> "$out/$mode.invocation.txt"
  timeout 30s "$@" < "$out/commands.txt" > "$out/$mode.stdout.txt" 2> "$out/$mode.stderr.txt" || code=$?
  printf 'exit_code %s\n' "$code" > "$out/$mode.exit.txt"
  printf '%s Step 1 TSan startup %s shell exit %s\n' "$(date -u +%FT%TZ)" "$mode" "$code" >> "$job/stamps.txt"
  cat "$out/$mode.stderr.txt"
  git add -- "$job"
  git commit -m "sol3 job 22 step 1 retain TSan startup $mode"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  ((code == 0)) && rg -Fxq uciok "$out/$mode.stdout.txt"
}
status=unavailable
launcher=none
if probe normal "$build"; then
  status=available
  launcher=normal
elif probe setarch_R setarch "$(uname -m)" -R "$build"; then
  status=available
  launcher=setarch_R
fi
printf '%s\n' "$status" > "$out/status.txt"
printf '%s\n' "$launcher" > "$out/launcher.txt"
printf '%s Step 1 TSan status %s launcher %s\n' "$(date -u +%FT%TZ)" "$status" "$launcher" >> "$job/stamps.txt"
git add -- "$job"
git commit -m "sol3 job 22 step 1 record TSan availability"
bash /workspace/work/sol3-job3/push-checkpoint.sh
