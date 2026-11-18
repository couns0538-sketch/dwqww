#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job22
build=/workspace/work/sol3-job22-build/build
controls="$job/controls"
attempted=()
expected=()

test_control() {
  local arm=$1
  local kind=$2
  local label=$arm
  local rc=0
  local attempt
  for attempt in 1 2 3; do
    if ((attempt > 1)); then label="$arm-startup-retry-$attempt"; fi
    bash "$job/run_case.sh" "$build/$arm/forge" au-d9 "$label" controls --count 1 || rc=$?
    local dest="$controls/$label"
    if python3 - "$dest/summary.json" <<'PY'
from pathlib import Path
import json
import sys
p=Path(sys.argv[1])
if not p.is_file():
    raise SystemExit(1)
d=json.loads(p.read_text())
raise SystemExit(int(not (d['startup_complete'] and d['engine_returncode'] not in (0,None)
                          and 'checksum 30ab43b4ba5db5f3' in d['net_active'])))
PY
    then
      attempted+=(--run "$label=$dest/engine.stderr.txt")
      expected+=(--expect "$label=$kind")
      return
    fi
    if [[ ! -f "$dest/engine.stderr.txt" ]] || ! rg -q '^AddressSanitizer:DEADLYSIGNAL' "$dest/engine.stderr.txt" ||        rg -q '^uciok$' "$dest/engine.stdout.txt"; then
      attempted+=(--run "$label=$dest/engine.stderr.txt")
      expected+=(--expect "$label=$kind")
      return
    fi
    attempted+=(--run "$label=$dest/engine.stderr.txt")
  done
  expected+=(--expect "$label=$kind")
}

test_control C-AU asan-heap
test_control C-UB ubsan-signed-overflow
case "$(cat "$job/T-startup/launcher.txt")" in
  normal) t_args=() ;;
  setarch_R) t_args=(--setarch-r) ;;
  none) t_args=() ;;
  *) exit 1 ;;
esac
if [[ "$(cat "$job/T-startup/status.txt")" == available ]]; then
  tlabel=C-T
  rc=0
  bash "$job/run_case.sh" "$build/C-T/forge" t-control "$tlabel" controls "${t_args[@]}" || rc=$?
  attempted+=(--run "$tlabel=$controls/$tlabel/engine.stderr.txt")
  if rg -q '^FATAL: ThreadSanitizer:' "$controls/$tlabel/engine.stderr.txt" &&      ! rg -q '^uciok$' "$controls/$tlabel/engine.stdout.txt"; then
    if [[ ! -f "$job/T-startup/setarch_R.exit.txt" ]]; then
      tlabel=C-T-setarch-R
      bash "$job/run_case.sh" "$build/C-T/forge" t-control "$tlabel" controls --setarch-r || rc=$?
      attempted+=(--run "$tlabel=$controls/$tlabel/engine.stderr.txt")
    fi
    if ! rg -q '^uciok$' "$controls/$tlabel/engine.stdout.txt"; then
      printf 'unavailable\n' > "$job/T-startup/status.txt"
      printf 'none\n' > "$job/T-startup/launcher.txt"
    else
      printf 'setarch_R\n' > "$job/T-startup/launcher.txt"
    fi
  fi
  if [[ "$(cat "$job/T-startup/status.txt")" == available ]]; then
    expected+=(--expect "$tlabel=tsan-race:SanitizerControlNodes")
  fi
fi
code=0
python3 -B "$job/parse_sanitizers.py" "${attempted[@]}" "${expected[@]}" --excerpts "$controls/excerpts.txt" \
  > "$controls/diagnostics.json" 2> "$controls/parser.stderr.txt" || code=$?
printf '%s Step 2 sanitizer control diagnostic gate exit %s, TSan %s\n' "$(date -u +%FT%TZ)" "$code" "$(cat "$job/T-startup/status.txt")" >> "$job/stamps.txt"
git add -- "$job"
git commit -m 'sol3 job 22 step 2 checkpoint deliberate checker controls and diagnostics'
bash /workspace/work/sol3-job3/push-checkpoint.sh
if ((code != 0)); then cat "$controls/parser.stderr.txt"; exit "$code"; fi
