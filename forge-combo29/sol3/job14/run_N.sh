#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job14
job=forge-combo29/sol3/job14
engine="$work/build_floor/forge"
net=/workspace/work/sol3-job4-net/net768.fnn3
old=forge-combo29/sol3/job13
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
cp "$work/run_N.sh" /workspace/work/sol3-job14-tools/summarize_arm.py "$job/"

compare() {
  local current=$1 baseline=$2 destination=$3
  python3 -B "$job/summarize_arm.py" "$current/rows.tsv" "$baseline/rows.tsv"     --candidate-stdout "$current/engine.stdout.txt" --baseline-stdout "$baseline/engine.stdout.txt"     > "$destination"
}

save() {
  local label=$1 status=$2
  date -u "+%FT%TZ $label exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$job"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 14 checkpoint $label"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

summarystats() {
  python3 - "$1" <<'PY'
import json
from pathlib import Path
import sys
r=json.loads(Path(sys.argv[1]).read_text())
print({k:r[k] for k in ('rows','nodes','node_ratio','first_three_nodes','nc0_sums','nc4_positive_positions','move_changes')})
PY
}

for suite in O G; do
  for fixture_group in K1 K2; do
    out="$job/$fixture_group/$suite"
    status=0
    compare "$out" "$job/K1/$suite" "$out/summary.json" || status=$?
    save "$fixture_group $suite summary relative to embedded Base5" "$status"
  done
done

run_arm() {
  local part=$1 suite=$2 setting=$3 out baseline status=0
  out="$job/$part/$suite/$setting"
  local args=(--depth 12 --counter)
  case "$setting" in
    Base4) args+=(--null-base 4) ;;
    Base3) args+=(--null-base 3) ;;
    Floor1) args+=(--null-floor 1) ;;
  esac
  baseline="$job/K1/$suite"
  if [ "$part" = N2 ]; then
    args+=(--net "$net")
    baseline="$job/N2/$suite/Base5"
  fi
  if (( $(date -u +%s) >= cutoff )); then
    return 124
  fi
  bash "$job/run_one.sh" "$engine" "$out" "$job/references/$suite.epd.txt" "${args[@]}" || status=$?
  if ((status == 0)); then
    compare "$out" "$baseline" "$out/summary.json" || status=$?
    if [ "$part/$suite/$setting" = N2/G/Base5 ]; then
      compare "$out" "$old/C2/counted" "$out/job13_C2_comparison.json" || status=$?
      python3 - "$out/job13_C2_comparison.json" <<'PY' > "$out/job13_C2_gate.txt" || status=$?
from pathlib import Path
import json
import sys
r=json.loads(Path(sys.argv[1]).read_text())
print(r['rows'],r['equal_search_labels'],r['equal_counter_rows'])
assert r['rows']==r['equal_search_labels']==r['equal_counter_rows']==353
PY
    fi
  fi
  save "$part $suite $setting raw and split move readback" "$status"
  if test -f "$out/summary.json"; then summarystats "$out/summary.json"; fi
  if ((status == 124)); then return "$status"; fi
}

for suite in O G; do
  for setting in Base4 Base3; do
    run_arm N1 "$suite" "$setting"
  done
done
for suite in G O; do
  for setting in Base5 Base4 Base3 Floor1; do
    run_arm N2 "$suite" "$setting"
  done
done
