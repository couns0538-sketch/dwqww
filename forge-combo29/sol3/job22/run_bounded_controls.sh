#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job22
build=/workspace/work/sol3-job22-build/build
controls="$job/controls"
args=(--run "C-AU=$controls/C-AU/engine.stderr.txt" --expect C-AU=asan-heap
      --run "C-UB=$controls/C-UB/engine.stderr.txt" --expect C-UB=ubsan-signed-overflow)
positive=0
for index in {1..5}; do
  label=C-T-pos-$index
  code=0
  bash "$job/run_case.sh" "$build/C-T/forge" t-control "$label" controls --control-position "$index" || code=$?
  dest="$controls/$label"
  args+=(--run "$label=$dest/engine.stderr.txt")
  if rg -q '^WARNING: ThreadSanitizer: data race' "$dest/engine.stderr.txt" &&
     rg -q 'SanitizerControlNodes' "$dest/engine.stderr.txt"; then
    args+=(--expect "$label=tsan-race:SanitizerControlNodes")
    positive=$((positive+1))
  fi
done
code=0
python3 -B "$job/parse_sanitizers.py" "${args[@]}" --excerpts "$controls/excerpts.txt" \
  > "$controls/diagnostics.json" 2> "$controls/parser.stderr.txt" || code=$?
if ((positive == 0)); then code=1; fi
printf '%s Step 2 sanitizer control diagnostic gate exit %s, %s of five bounded TSan searches named the counter\n' \
  "$(date -u +%FT%TZ)" "$code" "$positive" >> "$job/stamps.txt"
git add -- "$job"
git commit -m 'sol3 job 22 step 2 checkpoint independently bounded checker controls'
bash /workspace/work/sol3-job3/push-checkpoint.sh
if ((code != 0)); then cat "$controls/parser.stderr.txt"; exit "$code"; fi
