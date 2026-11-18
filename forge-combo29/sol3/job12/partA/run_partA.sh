#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job12
job=forge-combo29/sol3/job12
out="$job/partA"
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
export SOL3_WARM_CUTOFF
SOL3_WARM_CUTOFF=$(date -u -d "@$(($(date -u -d "$claim" +%s) + 2700))" +%FT%TZ)
mkdir -p "$out"/{A1,A2,A3,A4}
cp "$work/"{driver_hash.py,driver_hash.patch.txt,run_warm.sh,warm_readback.py,sum_counts.py,check_setup.py,check_resize.py,run_partA.sh} "$out/"
cp /workspace/work/sol3-job12-resize/{driver_resize.py,driver_resize.diff} "$out/A3/"
k11v=/workspace/work/sol3-job8/build_v/forge
k13=/workspace/work/sol3-job10/build_13/forge
counting=/workspace/work/sol3-job11/build_count/forge
control=/workspace/work/sol3-job10/build_C1/forge

save() {
  local label=$1 status=$2
  date -u "+%FT%TZ Part A $label exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$out" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 12 checkpoint $label"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

fixed() {
  local exe=$1 destination=$2 size=$3 left=$4 comparison=$5
  local status=0
  mkdir -p "$destination"
  bash "$out/run_warm.sh" "$exe" "$out/driver_hash.py" "$destination" --audit "$destination/observed" --hash-mib "$size" || status=$?
  if ((status == 0)); then
    python3 -B "$out/check_setup.py" "$destination" "$size" > "$destination/setup_check.txt" 2> "$destination/setup_check.stderr.txt" || status=$?
    PYTHONPATH="$work" python3 -B "$out/warm_readback.py" "$left" "$destination" "$comparison" > "$destination/readback.json" 2> "$destination/readback.stderr.txt" || status=$?
  fi
  return "$status"
}

for size in 1 4; do
  root="$out/A1/Hash$size"
  status=0
  fixed "$k11v" "$root/k11v" "$size" "$root/k11v" paired || status=$?
  save "A1 Hash $size k11v warm trace" "$status"
  test "$status" -eq 0
  fixed "$k13" "$root/k13" "$size" "$root/k11v" paired || status=$?
  save "A1 Hash $size k13 paired warm trace" "$status"
  if test -f "$root/k13/readback.json"; then cat "$root/k13/readback.json" "$root/k13/readback.stderr.txt"; fi
  test "$status" -eq 0
done

for size in 1 4; do
  run="$out/A2/Hash$size"
  status=0
  fixed "$counting" "$run" "$size" "$out/A1/Hash$size/k13" paired || status=$?
  if ((status == 0)); then
    PYTHONPATH="$work" python3 -B "$out/sum_counts.py" tt "$run" > "$run/totals.json" 2> "$run/totals.stderr.txt" || status=$?
  fi
  save "A2 Hash $size counted coverage" "$status"
  if test -f "$run/totals.json"; then cat "$run/totals.json" "$run/totals.stderr.txt"; fi
  test "$status" -eq 0
done

for arm in k11v k13; do
  status=0
  run="$out/A3/$arm"
  mkdir "$run"
  exe="$k11v"
  if [ "$arm" = k13 ]; then exe="$k13"; fi
  bash "$out/run_warm.sh" "$exe" "$out/A3/driver_resize.py" "$run" --resize-evidence "$run/resize.jsonl" || status=$?
  if ((status == 0)); then
    python3 -B "$out/check_resize.py" "$run/resize.jsonl" > "$run/resize_check.txt" 2> "$run/resize_check.stderr.txt" || status=$?
    PYTHONPATH="$work" python3 -B "$out/warm_readback.py" "$out/A3/k11v" "$run" paired > "$run/readback.json" 2> "$run/readback.stderr.txt" || status=$?
  fi
  save "A3 $arm resized Hash 16 to 4 at game 30" "$status"
  if test -f "$run/readback.json"; then cat "$run/readback.json" "$run/readback.stderr.txt"; fi
  test "$status" -eq 0
done

status=0
fixed "$control" "$out/A4" 1 "$out/A1/Hash1/k13" control || status=$?
if ((status == 0)); then
  python3 - "$out/A4/readback.json" <<'PY' > "$out/A4/gate.txt" 2> "$out/A4/gate.stderr.txt" || status=$?
import json
from pathlib import Path
import sys
result = json.loads(Path(sys.argv[1]).read_text())
old, new = result['baseline']['trace_fnv1a64'], result['candidate']['trace_fnv1a64']
print('legacy', old, new)
if old == new or result['first_legacy_difference'] is None:
    raise ValueError('C1 has not changed the Hash 1 legacy trace')
first = result['first_legacy_difference']
print(f'First legacy difference at row {first["row"]}')
for label in ('k13_reference', 'candidate'):
    row = first[label]
    print(f'{label} game={row["game"]} ply={row["ply"]} final_nodes={row["final"]}')
    for key in ('position', 'last_info', 'final_line', 'bestmove_line'):
        print(row[key])
PY
fi
save 'A4 Hash 1 planted owned hit mask' "$status"
if test -f "$out/A4/gate.txt"; then cat "$out/A4/gate.txt" "$out/A4/gate.stderr.txt"; fi
test "$status" -eq 0
