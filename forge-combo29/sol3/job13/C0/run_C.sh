#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job13
work=/workspace/work/sol3-job13
patch_source=/workspace/work/sol3-job13-count
base=/workspace/work/sol3-job12/tree_F
kF=/workspace/work/sol3-job12/build_F/forge
net=/workspace/work/sol3-job4-net/net768.fnn3
p="$job/references/P.fen.txt"
g="$job/references/fixture_G.epd.txt"
mkdir "$job/C0"
cp "$patch_source/null_count.patch.txt" "$job/"
cp "$patch_source/diff_receipt.txt" "$job/C0/"
cp "$work/verify_counters_raw.py" "$work/run_C.sh" "$job/C0/"
sha256sum "$job/null_count.patch.txt" > "$job/C0/patch.sha256.txt"
cp -a "$base" "$work/tree_nc"
patch -d "$work/tree_nc" -p1 -F0 --batch --forward < "$job/null_count.patch.txt" > "$job/C0/patch_apply.txt" 2>&1
if rg -in 'offset|fuzz|reject|failed' "$job/C0/patch_apply.txt"; then exit 1; fi
diff -rq "$patch_source/tree" "$work/tree_nc" > "$job/C0/reproduction.txt"
save() {
  local label=$1 status=$2
  date -u "+%FT%TZ $label exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$job"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 13 checkpoint $label"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}
save 'C0 froze independent null-count patch and clean application' 0
status=0
bash /workspace/work/sol3-job3/build_one.sh "$work/tree_nc" "$work/build_nc" "$job/C0/build_nc.txt" || status=$?
save 'C0 compiled independent null-count build' "$status"
test "$status" -eq 0
counted="$work/build_nc/forge"

for arm in builtin net768; do
  destination="$job/C0/P_$arm"
  original="$job/A1/rows.tsv"
  args=(--ladder 16 --counter)
  if [ "$arm" = net768 ]; then
    original="$job/B1/rows.tsv"
    args+=(--net "$net")
  fi
  head -n 17 "$original" > "$work/first16_$arm.tsv"
  status=0
  bash "$job/run_one.sh" "$counted" "$destination" "$p" "${args[@]}" || status=$?
  if ((status == 0)); then
    python3 -B "$job/readback.py" identity "$destination/rows.tsv" "$work/first16_$arm.tsv" > "$destination/identity.json" || status=$?
    python3 -B "$job/C0/verify_counters_raw.py" "$destination" 16 > "$destination/verified_raw.json" || status=$?
    if [ "$arm" = builtin ]; then
      python3 - "$destination/verified_raw.json" <<'PY' > "$destination/depth16_gate.txt" || status=$?
import json
from pathlib import Path
import sys
info = json.loads(Path(sys.argv[1]).read_text())
print('NC0 at P depth 16', *info['last_row_counters'])
assert info['last_row_counters'][4] >= 1, 'P depth 16 did not expose any shallow null cutoff with quiet mate'
PY
    fi
  fi
  save "C0 $arm P depth 1 through 16 node and move control" "$status"
  if test -f "$destination/depth16_gate.txt"; then cat "$destination/depth16_gate.txt"; fi
  test "$status" -eq 0
done

for arm in C1 C2; do
  destination="$job/$arm"
  args=(--depth 12)
  if [ "$arm" = C2 ]; then args+=(--net "$net"); fi
  status=0
  bash "$job/run_one.sh" "$kF" "$destination/plain" "$g" "${args[@]}" || status=$?
  if ((status == 0)) && [ "$arm" = C1 ]; then
    python3 -B "$job/readback.py" Gref "$destination/plain/rows.tsv" "$job/references/G_base_d12.tsv" > "$destination/reference_comparison.json" || status=$?
    cat "$destination/reference_comparison.json"
  fi
  save "$arm G uninstrumented baseline" "$status"
  test "$status" -eq 0
  bash "$job/run_one.sh" "$counted" "$destination/counted" "$g" "${args[@]}" --counter || status=$?
  if ((status == 0)); then
    python3 -B "$job/readback.py" identity "$destination/counted/rows.tsv" "$destination/plain/rows.tsv" > "$destination/identity.json" || status=$?
    python3 -B "$job/C0/verify_counters_raw.py" "$destination/counted" 353 > "$destination/counted/sums.json" || status=$?
  fi
  save "$arm G instrumented counts and identity" "$status"
  if test -f "$destination/counted/sums.json"; then cat "$destination/counted/sums.json"; fi
  test "$status" -eq 0
done
