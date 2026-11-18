#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job15
job=forge-combo29/sol3/job15
old=forge-combo29/sol3/job14
refs=/workspace/work/sol3-job15-reference
engine="$work/build_guard/forge"
mkdir -p "$job/references"
cp "$work/"{fixed_depth.py,readback.py,known_compare.py,verify_counters_raw.py,run_one.sh,check_identity.py,run_K.sh} "$job/"
cp /workspace/work/sol3-job14-tools/summarize_arm.py /workspace/work/sol3-job15-tools/audit_guard.py "$job/"
for item in O.epd.txt G.epd.txt P.fen.txt; do
  git show HEAD:"$old/references/$item" > "$job/references/$item"
done
cp "$refs/"{O.tsv,G.tsv,P.tsv,P.raw.txt,O.tsv.meta,G.tsv.meta,P.meta,checks.txt,reference_proof.txt} "$job/references/"
cat > "$job/references/source.txt" <<'EOF'
O, G and P fixture commands are exact copies of Job 14.
O uses the reference EPD convention with 0 1 clocks. G already has 0 1 clocks.
Guard-on PC20 references are Astra5 Job 5 Part A at edf7851d3ba16ea9f00be7665accb091b21b5781, under forge-combo29/astra5/job5/A/one.
Only result files were opened. The peer's source patch was not opened.
EOF
sha256sum "$job/references/"*.tsv "$job/references/"*.epd.txt "$job/references/P.fen.txt" > "$job/references/hashes.txt"
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

for step in K1 K2; do
  for suite in O G; do
    destination="$job/$step/$suite"
    status=0
    guard=0
    if [ "$step" = K2 ]; then guard=1; fi
    bash "$job/run_one.sh" "$engine" "$destination" "$job/references/$suite.epd.txt" --depth 12 --counter --null-guard "$guard" || status=$?
    if ((status == 0)); then
      quantity=$(wc -l < "$job/references/$suite.epd.txt")
      python3 -B "$job/verify_counters_raw.py" "$destination" "$quantity" > "$destination/raw_counts.json" 2> "$destination/raw_counts.stderr.txt" || status=$?
      if [ "$step" = K1 ]; then
        summarize "$destination" "$old/K1/$suite" "$destination/job14_comparison.json" || status=$?
        python3 -B "$job/check_identity.py" "$destination/job14_comparison.json" "$quantity" > "$destination/known_gate.txt" 2> "$destination/known_gate.stderr.txt" || status=$?
        summarize "$destination" "$destination" "$destination/summary.json" || status=$?
      else
        python3 -B "$job/known_compare.py" "$job/references/$suite.tsv" "$destination/rows.tsv" > "$destination/known_gate.json" 2> "$destination/known_gate.stderr.txt" || status=$?
        summarize "$destination" "$job/K1/$suite" "$destination/summary.json" || status=$?
        python3 -B "$job/audit_guard.py" "$job/K1/$suite/rows.tsv" "$destination/rows.tsv" > "$destination/K4_K5.json" 2> "$destination/K4_K5.stderr.txt" || status=$?
      fi
    fi
    save "$step $suite PC20 known result and guard invariance" "$status"
    if test -f "$destination/known_gate.json"; then cat "$destination/known_gate.json"; fi
    if test -f "$destination/known_gate.txt"; then cat "$destination/known_gate.txt"; fi
  done
done
destination="$job/K3/P"
status=0
bash "$job/run_one.sh" "$engine" "$destination" "$job/references/P.fen.txt" --ladder 20 --counter --null-guard 1 || status=$?
if ((status == 0)); then
  python3 -B "$job/readback.py" A1 "$destination/rows.tsv" "$job/references/P.tsv" > "$destination/known_gate.json" 2> "$destination/known_gate.stderr.txt" || status=$?
  python3 -B "$job/readback.py" ladder "$destination/rows.tsv" > "$destination/threshold.json" || status=$?
  python3 -B "$job/verify_counters_raw.py" "$destination" 20 > "$destination/raw_counts.json" 2> "$destination/raw_counts.stderr.txt" || status=$?
  python3 -B "$job/audit_guard.py" "$destination/rows.tsv" "$destination/rows.tsv" > "$destination/K4.json" 2> "$destination/K4.stderr.txt" || status=$?
fi
save 'K3 P guard-on known ladder and K4' "$status"
if test -f "$destination/known_gate.json"; then cat "$destination/known_gate.json" "$destination/threshold.json"; fi
