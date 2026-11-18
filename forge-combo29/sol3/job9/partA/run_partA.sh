#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job9
work=/workspace/work/sol3-job9
out="$job/partA"
previous=forge-combo29/sol3/job8
net=/workspace/work/sol3-job4-net/net768.fnn3
driver="$previous/step2/driver_verify.py"
git show HEAD:forge-combo29/sol3/job6/trace_tools.py > "$work/trace_tools.py"
remaining=$(date -u -d 2026-11-18T12:04:36Z +%s)
remaining=$((remaining - $(date -u +%s)))
args=(--engine "$work/build_count/forge" --net "$net" --games 60 --softnodes 2000 --random-plies 8 --max-plies 300
      --seed 20261117 --json --trace "$out/trace.jsonl" --audit "$out/observed")
{
  printf 'python3 -B %q' "$driver"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$work/build_count/forge" "$driver" "$net" "$previous/step1/trace.jsonl"
  date -u +%FT%TZ
} > "$out/run.meta"
status=0
if ((remaining > 0)); then
  timeout --kill-after=5s "$remaining" python3 -B "$driver" "${args[@]}" > "$out/summary.json" 2> "$out/driver.stderr.txt" || status=$?
else
  status=124
fi
if ((status == 0)); then
  python3 -B "$work/trace_tools.py" summary "$out/trace.jsonl" > "$out/readback.json" || status=$?
  python3 -B "$work/trace_tools.py" compare "$previous/step1/trace.jsonl" "$out/trace.jsonl" > "$out/first_difference.json" || status=$?
  if ((status == 0)); then
    python3 -B "$out/sum_paths.py" "$out" "$previous/step1" > "$out/totals.json" 2> "$out/totals.stderr.txt" || status=$?
  fi
fi
printf 'exit_code %s\n' "$status" >> "$out/run.meta"
date -u "+%FT%TZ Part A ran and checked counts against complete observed warm UCI output, exit $status" >> "$job/stamps.txt"
git add --sparse -- "$out" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 9 part A checkpoint per-search counts and warm trace'
bash /workspace/work/sol3-job3/push-checkpoint.sh
if test -f "$out/totals.json"; then cat "$out/totals.json" "$out/totals.stderr.txt"; fi
test "$status" -eq 0
