#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job12
job=forge-combo29/sol3/job12
out="$job/B3"
status=0
test -f "$job/B2/classification.txt"
rg -q '^gate PASS$' "$job/B2/classification.txt"
mkdir -p "$out"/{pins,warm,cold}
cp "$work/run_B3.sh" "$out/"
git show HEAD:forge-combo29/sol3/job7/identity.py > "$work/identity.py"
git show HEAD:forge-combo29/sol3/job7/compare_limits.py > "$work/compare_limits.py"
git show HEAD:forge-combo29/sol3/job11/stage0/check_pins.py |   sed -e 's/k13, k14 = map/k13, kF = map/' -e "s/('k14', k14)/('kF', kF)/" > "$out/pins/check_pins.py"
git show HEAD:forge-combo29/sol3/job11/B2/check_cold.py | sed 's/k14f/kFf/g; s/Job 11/Job 12/g' > "$out/cold/check_cold.py"
git show HEAD:forge-combo29/sol3/job11/B2/run_cold.sh |   sed 's/sol3-job11/sol3-job12/g; s/2026-11-18T13:35:02Z/2026-11-18T14:02:20Z/g' > "$out/cold/run_cold.sh"
git show HEAD:forge-combo29/sol3/job5/probe.diff > "$out/cold/job5_probe.patch.txt"

save() {
  local label=$1 status=$2
  date -u "+%FT%TZ Part B3 $label exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$out" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 12 checkpoint B3 $label"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

net=/workspace/work/sol3-job4-net/net768.fnn3
k13=/workspace/work/sol3-job10/build_13/forge
kF="$work/build_F/forge"
bash /workspace/work/sol3-job3/build_one.sh "$work/tree_F" "$work/build_F" "$out/pins/build_F.txt" || status=$?
if ((status == 0)); then
  sha256sum "$kF" "$k13" "$net" > "$out/pins/input_hashes.txt"
  PYTHONPATH="$work" python3 -B "$out/pins/check_pins.py" "$out/pins" "$net" "$k13" "$kF" > "$out/pins/pins.txt" 2> "$out/pins/pins.stderr.txt" || status=$?
fi
save 'kF build and five pins' "$status"
if test -f "$out/pins/pins.txt"; then cat "$out/pins/pins.txt" "$out/pins/pins.stderr.txt"; fi
test "$status" -eq 0

bash "$job/partA/run_warm.sh" "$kF" "$work/driver_final.py" "$out/warm" || status=$?
if ((status == 0)); then
  PYTHONPATH="$work" python3 -B "$job/partA/warm_readback.py" forge-combo29/sol3/job10/step1 "$out/warm" equal > "$out/warm/readback.json" 2> "$out/warm/readback.stderr.txt" || status=$?
fi
save 'kF Hash 16 warm trace' "$status"
if test -f "$out/warm/readback.json"; then cat "$out/warm/readback.json" "$out/warm/readback.stderr.txt"; fi
test "$status" -eq 0

cp -a "$work/tree_F" "$work/tree_Ff"
patch -d "$work/tree_Ff" -p1 -F0 --batch --forward < "$out/cold/job5_probe.patch.txt" > "$out/cold/patch_apply.txt" 2>&1 || status=$?
if rg -in 'fuzz|reject|failed' "$out/cold/patch_apply.txt"; then status=1; fi
if ((status == 0)); then
  bash /workspace/work/sol3-job3/build_one.sh "$work/tree_Ff" "$work/build_Ff" "$out/cold/build_Ff.txt" || status=$?
fi
if ((status == 0)); then
  sha256sum "$work/build_Ff/forge" "$out/cold/job5_probe.patch.txt" "$work/compare_limits.py" > "$out/cold/build_and_helper.sha256.txt"
fi
save 'kFf build with exact probe' "$status"
test "$status" -eq 0
fixture=forge-combo29/sol3/job3/positions.txt
prior=forge-combo29/sol3/job7
status_all=0
for limit in 50000 250000; do
  mkdir "$out/cold/$limit"
  for cell in B2 N2; do
    candidate="$out/cold/$limit/$cell"
    status=0
    bash "$out/cold/run_cold.sh" "$work/build_Ff/forge" "$candidate" "$limit" "$cell" || status=$?
    if ((status == 0)); then
      PYTHONPATH="$work" python3 -B "$out/cold/check_cold.py" "$fixture" "$prior" "$candidate" "$limit" "$cell" > "$candidate/gate.txt" 2> "$candidate/gate.stderr.txt" || status=$?
      cat "$candidate/gate.txt" "$candidate/gate.stderr.txt"
    fi
    save "kFf $cell $limit cold labels" "$status"
    if ((status != 0)); then status_all=$status; fi
  done
done
test "$status_all" -eq 0
