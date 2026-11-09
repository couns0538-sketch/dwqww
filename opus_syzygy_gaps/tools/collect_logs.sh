#!/usr/bin/env bash
# collect_logs.sh <frozen tag> <suite tag> <after_w6 tag> <info tag> - copies the compact result files of the frozen head from out/ into logs/ of the pack. Only small text results, never exes or row files.
# Prints each file it could not find, so a missing result shows. Run again after any rerun.
set -u
J=/d/forge_jobs_20261107/opus1
L=$J/repo/opus_syzygy_gaps/logs
f=$1; s=$2; w=$3; i=$4
miss=0
cp1() { # cp1 <source under out/> <name in logs/>
  if [ -f "$J/out/$1" ]; then cp "$J/out/$1" "$L/$2"; else echo "missing out/$1"; miss=$((miss + 1)); fi
}
cp1 "logs/final_chain_$f.txt" "final_chain_$f.txt"
cp1 "builds/final_$f.txt" "final_$f.txt"
cp1 "builds/macro_combos_$f.txt" "macro_combos_$f.txt"
cp1 "builds/lint_$f.txt" "lint_$f.txt"
cp1 "builds/repro_$f.txt" "repro_$f.txt"
cp1 "builds/after_w6_$f.txt" "after_w6_${f}_rejected.txt"
cp1 "builds/after_w6_$f.txt.patch.log" "after_w6_${f}_rejected.patch.log"
cp1 "builds/after_w6_$w.txt" "after_w6_$w.txt"
cp1 "builds/after_w6_$w.txt.arms" "after_w6_$w.arms.txt"
cp1 "ident/buildB_c$f/COMPARE.txt" "identity_buildB_c$f.txt"
cp1 "builds/buildB_c${f}_pc1/SUMMARY.txt" "kit_buildB_c${f}_pc1.txt"
cp1 "builds/buildA_c$f/SUMMARY.txt" "kit_buildA_c$f.txt"
cp1 "builds/w6p6_parent_$w/SUMMARY.txt" "kit_w6p6_parent_$w.txt"
cp1 "builds/w6p6_B_$w/SUMMARY.txt" "kit_w6p6_B_$w.txt"
cp1 "qual/${s}on/SUMMARY.txt" "suite_${s}on.txt"
cp1 "qual/${s}on/special2.txt" "suite_${s}on_special2.txt"
cp1 "qual/${s}on/move_quality.json" "suite_${s}on_move_quality.json"
cp1 "qual/info_$i/SUMMARY.txt" "info_$i.txt"
cp1 "qual/p6/SUMMARY.txt" "suite_parent.txt"
cp1 "exp/partial/${s}on/SUMMARY.txt" "partial_${s}on.txt"
cp1 "san/$s/runs/SUMMARY.txt" "san_$s.txt"
cp1 "san/$s/flips/SUMMARY.txt" "flips_$s.txt"
cp1 "exp/hunt/churn_$s/SUMMARY.txt" "churn_$s.txt"
cp1 "exp/hunt/green_v8.txt" "green_v8.txt"
cp1 "hunt_agent/FINDINGS.md" "hunt_agent_findings.md"
# the row files of a failed compare, never the whole set
for d in "$J"/out/logs/pred1_"$s".log "$J"/out/logs/pred2_"$s".log; do [ -f "$d" ] && cp "$d" "$L/$(basename "$d")" || { echo "missing $d"; miss=$((miss + 1)); }; done
echo "collect_logs: missing $miss"
du -sh "$L" | cut -f1
