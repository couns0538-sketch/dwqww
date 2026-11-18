#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job11
job=forge-combo29/sol3/job11
out="$job/B4"
rg 'B3 .* exit 0$' "$job/stamps.txt"
mkdir -p "$out"/{C1,C2,C3,C4,C5}
cp "$work/"{run_B4.sh,make_repetition_controls.py,check_control.py} "$out/"
cp "$work/oracle_patches/"*.patch.txt "$out/"
sha256sum "$out/"*.patch.txt > "$out/patches.sha256.txt"
date -u '+%FT%TZ B4 froze four required controls and optional null-prefix control before all control builds' >> "$job/stamps.txt"
git add --sparse -- "$out" "$job/stamps.txt"
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
git commit -qm 'sol3 job 11 B4 freeze five one-line repetition controls'
bash /workspace/work/sol3-job3/push-checkpoint.sh

overall=0
for arm in C1 C2 C3 C4 C5; do
  destination="$out/$arm"
  tree="$work/tree_$arm"
  build="$work/build_$arm"
  cp -a "$work/tree_B3" "$tree"
  patch -d "$tree" -p1 -F0 --batch --forward < "$out/$arm.patch.txt" > "$destination/patch_apply.txt" 2>&1
  if rg -in 'offset|fuzz|reject|failed' "$destination/patch_apply.txt"; then exit 1; fi
  diff -qr "$work/tree_B3" "$tree" > "$destination/source_difference.txt" || test "$?" -eq 1
  test "$(wc -l < "$destination/source_difference.txt")" -eq 1
  status=0
  driver_exit=0
  gate_status=0
  bash /workspace/work/sol3-job3/build_one.sh "$tree" "$build" "$destination/build.txt" || status=$?
  if ((status == 0)); then
    bash "$job/partA/run_warm.sh" "$build/forge" "$job/B3/driver_rep.py" "$destination" --audit "$destination/observed" || driver_exit=$?
    python3 -B "$out/check_control.py" "$arm" "$destination" "$driver_exit" > "$destination/gate.txt" 2> "$destination/gate.stderr.txt" || gate_status=$?
    if ((gate_status == 4)); then
      PYTHONPATH="$work" python3 -B "$job/partA/warm_readback.py" "$job/B1" "$destination" equal > "$destination/readback.json" 2> "$destination/readback.stderr.txt" || status=$?
      PYTHONPATH="$work" python3 -B "$job/partA/sum_counts.py" rep "$destination" > "$destination/totals.json" 2> "$destination/totals.stderr.txt" || status=$?
    elif ((gate_status != 0)); then
      status=$gate_status
    fi
  fi
  date -u "+%FT%TZ B4 $arm driver exit $driver_exit reporter $gate_status status $status" >> "$job/stamps.txt"
  git add --sparse -- "$destination" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 11 B4 checkpoint $arm repetition control"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if test -f "$destination/gate.txt"; then cat "$destination/gate.txt" "$destination/gate.stderr.txt"; fi
  if ((status != 0)); then overall=$status; fi
done
test "$overall" -eq 0
