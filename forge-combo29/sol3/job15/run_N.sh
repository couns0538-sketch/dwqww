#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job15
job=forge-combo29/sol3/job15
engine="$work/build_guard/forge"
net=/workspace/work/sol3-job4-net/net768.fnn3
old14=forge-combo29/sol3/job14
old13=forge-combo29/sol3/job13
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
cp "$work/run_N.sh" "$job/"

save() {
  local label=$1 status=$2
  date -u "+%FT%TZ $label exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$job"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 15 checkpoint $label"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

summarize() {
  local current=$1 baseline=$2 out=$3
  python3 -B "$job/summarize_arm.py" "$current/rows.tsv" "$baseline/rows.tsv"     --candidate-stdout "$current/engine.stdout.txt" --baseline-stdout "$baseline/engine.stdout.txt" > "$out"
}

run_arm() {
  local part=$1 suite=$2 guard=$3 out baseline status=0 known="$old14/N2/$2/Base5"
  local fixture="$job/references/$suite.epd.txt"
  local args=(--depth 12)
  if [ "$suite" = P ]; then
    fixture="$job/references/P.fen.txt"
    args=(--ladder 20)
  fi
  out="$job/$part/$suite/Guard$guard"
  baseline="$job/$part/$suite/Guard0"
  if (( $(date -u +%s) >= cutoff )); then return 124; fi
  bash "$job/run_one.sh" "$engine" "$out" "$fixture" "${args[@]}" --counter --net "$net" --null-guard "$guard" || status=$?
  if ((status == 0)); then
    summarize "$out" "$baseline" "$out/summary.json" || status=$?
    if [ "$guard" = 0 ] && [ "$suite" != P ]; then
      summarize "$out" "$known" "$out/job14_comparison.json" || status=$?
      python3 -B "$job/check_identity.py" "$out/job14_comparison.json" "$(wc -l < "$fixture")" > "$out/job14_gate.txt" 2> "$out/job14_gate.stderr.txt" || status=$?
    elif [ "$guard" = 0 ] && [ "$suite" = P ]; then
      python3 -B "$job/readback.py" identity "$out/rows.tsv" "$old13/B1/rows.tsv" > "$out/job13_P_comparison.json" 2> "$out/job13_P_comparison.stderr.txt" || status=$?
    elif [ "$guard" = 1 ]; then
      python3 -B "$job/audit_guard.py" "$baseline/rows.tsv" "$out/rows.tsv" > "$out/K4_K5.json" 2> "$out/K4_K5.stderr.txt" || status=$?
    fi
    if [ "$suite" = P ]; then
      python3 -B "$job/readback.py" ladder "$out/rows.tsv" > "$out/threshold.json" 2> "$out/threshold.stderr.txt" || status=$?
    fi
  fi
  save "$part $suite Guard$guard raw labels and invariance" "$status"
  if test -f "$out/summary.json"; then
    python3 - "$out/summary.json" <<'PY'
import json
from pathlib import Path
import sys
r=json.loads(Path(sys.argv[1]).read_text())
print({k:r[k] for k in ('rows','nodes','node_ratio','first_three_nodes','nc0_sums','nc4_positive_positions','move_changes')})
PY
  fi
  if test -f "$out/K4_K5.json"; then
    python3 - "$out/K4_K5.json" <<'PY'
import json
from pathlib import Path
import sys
r=json.loads(Path(sys.argv[1]).read_text())
print({k:r[k] for k in ('k4_passed','k5_passed','guard_on_nc4_positive','unflagged_node_or_move_changes')})
PY
  fi
  if ((status == 124)); then return "$status"; fi
}

for suite in G O; do
  run_arm N1 "$suite" 0
  run_arm N1 "$suite" 1
done
if (( $(date -u +%s) < cutoff )); then
  run_arm N2 P 0
  run_arm N2 P 1
fi
