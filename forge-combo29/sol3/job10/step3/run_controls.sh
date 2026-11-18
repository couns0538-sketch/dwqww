#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job10
job=forge-combo29/sol3/job10
out="$job/step3"
derive_status=0
for arm in C1 C2 C3; do
  destination="$out/$arm"
  tree="$work/tree_$arm"
  build="$work/build_$arm"
  cp -a "$work/tree_13" "$tree"
  patch -d "$tree" -p1 -F0 --batch --forward < "$out/$arm.patch.txt" > "$destination/patch_apply.txt" 2>&1
  if rg -in 'offset|fuzz|reject|failed' "$destination/patch_apply.txt"; then exit 1; fi
  diff -qr "$work/tree_13" "$tree" > "$destination/source_difference.txt" || test "$?" -eq 1
  test "$(wc -l < "$destination/source_difference.txt")" -eq 1

  status=0
  bash /workspace/work/sol3-job3/build_one.sh "$tree" "$build" "$destination/build.txt" || status=$?
  if ((status == 0)); then
    bash "$job/step1/run_warm.sh" "$build/forge" "$work/driver_final.py" "$destination" || status=$?
  fi
  if ((status == 0)); then
    PYTHONPATH="$work" python3 -B "$job/step1/warm_readback.py" "$job/step1" "$destination" control > "$destination/readback.json" 2> "$destination/readback.stderr.txt" || status=$?
  fi
  needs_fallback=0
  if ((status == 0)); then
    python3 - "$arm" "$destination/readback.json" <<'PY' > "$destination/warm_gate.txt" || needs_fallback=$?
import json
from pathlib import Path
import sys
arm, path = sys.argv[1:]
result = json.loads(Path(path).read_text())
left, right = result['baseline']['trace_fnv1a64'], result['candidate']['trace_fnv1a64']
print(f'{arm} legacy reference {left} candidate {right}')
if left == right:
    print('No legacy hash change; run N2 at 250000 hard nodes.')
    raise SystemExit(4)
first = result['first_legacy_difference']
print(f'First legacy difference at row {first["row"]}')
for label in ('k13_reference', 'candidate'):
    row = first[label]
    print(f'{label} game={row["game"]} ply={row["ply"]} final_nodes={row["final"]}')
    print(row['position'])
    print(row['last_info'])
    print(row['final_line'])
    print(row['bestmove_line'])
PY
  fi
  if ((needs_fallback != 0 && needs_fallback != 4)); then status=$needs_fallback; fi

  if ((status == 0 && needs_fallback == 4)); then
    probe_tree="$work/tree_${arm}f"
    probe_build="$work/build_${arm}f"
    cp -a "$tree" "$probe_tree"
    patch -d "$probe_tree" -p1 -F0 --batch --forward < "$job/step2/job5_probe.patch.txt" > "$destination/fallback_patch.txt" 2>&1 || status=$?
    if ((status == 0)); then
      bash /workspace/work/sol3-job3/build_one.sh "$probe_tree" "$probe_build" "$destination/fallback_build.txt" || status=$?
    fi
    if ((status == 0)); then
      bash "$job/step2/run_cold.sh" "$probe_build/forge" "$destination/fallback_N2" 250000 N2 || status=$?
    fi
    if ((status == 0)); then
      compare_status=0
      PYTHONPATH="$work" python3 -B "$job/step2/check_cold.py" forge-combo29/sol3/job3/positions.txt "$job/step2/250000/N2" "$destination/fallback_N2" 250000 N2 > "$destination/fallback_gate.txt" 2> "$destination/fallback_gate.stderr.txt" || compare_status=$?
      if ((compare_status == 0)); then
        printf '%s\n' 'Path not shown by the two workloads.' >> "$destination/fallback_gate.txt"
      elif ! rg -q 'rows=389 equal=[0-9]+ ' "$destination/fallback_gate.txt"; then
        status=$compare_status
      fi
    fi
  fi
  date -u "+%FT%TZ Step 3 $arm owned-table control warm trace and conditional cold gate exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$destination" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 10 step 3 checkpoint $arm warm control"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if test -f "$destination/warm_gate.txt"; then cat "$destination/warm_gate.txt"; fi
  if test -f "$destination/fallback_gate.txt"; then cat "$destination/fallback_gate.txt" "$destination/fallback_gate.stderr.txt"; fi
  if ((status != 0)); then derive_status=$status; fi
done
test "$derive_status" -eq 0
