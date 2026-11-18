#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job11
work=/workspace/work/sol3-job11
out="$job/partA"
baseline=forge-combo29/sol3/job10/step1
observer=forge-combo29/sol3/job8/step2/driver_verify.py
cp "$work/sum_counts.py" "$out/"
git show HEAD:forge-combo29/sol3/job10/step1/warm_readback.py > "$out/warm_readback.py"
export SOL3_WARM_CUTOFF
SOL3_WARM_CUTOFF=$(date -u -d '+30 minutes' +%FT%TZ)
status=0
bash "$out/run_warm.sh" "$work/build_count/forge" "$observer" "$out" --audit "$out/observed" || status=$?
if ((status == 0)); then
  PYTHONPATH="$work" python3 -B "$out/warm_readback.py" "$baseline" "$out" equal > "$out/readback.json" 2> "$out/readback.stderr.txt" || status=$?
  PYTHONPATH="$work" python3 -B "$out/sum_counts.py" tt "$out" > "$out/totals.json" 2> "$out/totals.stderr.txt" || status=$?
fi
date -u "+%FT%TZ Part A counted owned TT probe, store and replacement paths across warm workload, exit $status" >> "$job/stamps.txt"
git add --sparse -- "$out" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 11 part A checkpoint TT coverage and first full cluster'
bash /workspace/work/sol3-job3/push-checkpoint.sh
if test -f "$out/totals.json"; then cat "$out/totals.json" "$out/totals.stderr.txt"; fi
test "$status" -eq 0
