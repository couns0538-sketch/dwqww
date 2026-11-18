#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job6
job=forge-combo29/sol3/job6
prev=/workspace/work/sol3-job4
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T11:02:40Z +%s)
mkdir "$root/stage2"
for arm in 0 10 11 12 P; do
  exe="$prev/build_$arm/forge"
  if [ "$arm" = 12 ]; then exe="$root/build_12/forge"; fi
  out="$root/stage2/arm_$arm"
  trace="$out.trace.jsonl"
  args=(--engine "$exe" --net "$net" --games 60 --softnodes 2000 --random-plies 8 --max-plies 300 --seed 20261117 --json --trace "$trace")
  {
    printf 'python3 -B %q' "$job/driver_final.py"
    printf ' %q' "${args[@]}"
    printf '\n'
    sha256sum "$exe" "$net" "$job/driver_final.py"
    printf 'uci\nquit\n' | "$exe" | sed -n '/^id name /p'
    date -u +%FT%TZ
  } > "$out.meta"
  status=0
  remaining=$((cutoff - $(date -u +%s)))
  if ((remaining > 0)); then
    timeout --kill-after=5s "$remaining" python3 -B "$job/driver_final.py" "${args[@]}" > "$out.json" 2> "$out.stderr.txt" || status=$?
  else
    status=124
  fi
  if [ "$status" -eq 0 ]; then
    python3 -B "$job/trace_tools.py" summary "$trace" > "$out.readback.json"
    if [ "$arm" != 0 ]; then
      python3 -B "$job/trace_tools.py" compare "$root/stage2/arm_0.trace.jsonl" "$trace" > "$out.first_difference.json"
    fi
    python3 - "$out" "$arm" "$root/stage1/r15d_step1.json" <<'PY' > "$out.gate.txt" 2> "$out.gate.stderr.txt" || status=$?
import json
from pathlib import Path
import sys
stem, arm, baseline_path = sys.argv[1:]
row=json.loads(Path(stem+'.json').read_text())
readback=json.loads(Path(stem+'.readback.json').read_text())
keys=('searches','total_nodes','trace_fnv1a64','terminal','final_sum','at_cap','final_fnv1a64')
assert all(row[key] == readback[key] for key in keys)
if arm=='0':
    baseline=json.loads(Path(baseline_path).read_text())
    assert all(row[key] == baseline[key] for key in keys)
if arm=='11':
    assert row['at_cap'] > 0, 'Control cannot fire: k11 never hit the hard cap'
if arm=='P':
    k11=json.loads(Path(stem).with_name('arm_11.json').read_text())
    assert row['final_fnv1a64'] != k11['final_fnv1a64'], 'Planted final trace did not change'
print({key:row[key] for key in keys})
PY
    sha256sum "$trace" >> "$out.meta"
  fi
  printf 'exit_code %s\n' "$status" >> "$out.meta"
  for file in "$out".*; do
    if [[ "$file" != *.trace.jsonl ]]; then cp "$file" "$job/"; fi
  done
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 2 warm final-count arm $arm exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "sol3 job 6 step 2 checkpoint warm arm $arm"
  if [ "$status" -eq 0 ]; then cat "$out.gate.txt"; else cat "$out.stderr.txt" "$out.gate.stderr.txt" 2>/dev/null || true; fi
  test "$status" -eq 0
done
