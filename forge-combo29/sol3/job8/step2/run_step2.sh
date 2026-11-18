#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job8
job=forge-combo29/sol3/job8
step="$job/step2"
cp "$work/check_verify.py" "$step/"
baseline="$job/step1/trace.jsonl"
step_status=0
for arm in verify C1 C2 C3; do
  out="$step/$arm"
  driver_status=0
  status=0
  bash "$job/step1/run_warm.sh" "$work/build_$arm/forge" "$step/driver_verify.py" "$out" --audit "$out/observed" || driver_status=$?
  if [ "$arm" = verify ] && [ "$driver_status" -eq 0 ]; then
    python3 -B "$work/trace_tools.py" summary "$out/trace.jsonl" > "$out/readback.json" || status=$?
    python3 -B "$work/trace_tools.py" compare "$baseline" "$out/trace.jsonl" > "$out/first_difference.json" || status=$?
  fi
  python3 -B "$step/check_verify.py" "$arm" "$out" "$driver_status" > "$out/gate.txt" 2> "$out/gate.stderr.txt" || status=$?
  date -u "+%FT%TZ Step 2 $arm observed driver exit $driver_status and gate exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$out" "$step/check_verify.py" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 8 step 2 checkpoint $arm verification workload"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  cat "$out/gate.txt" "$out/gate.stderr.txt"
  if [ "$status" -ne 0 ]; then
    step_status=$status
    if [ "$arm" = verify ]; then break; fi
  fi
done
test "$step_status" -eq 0
