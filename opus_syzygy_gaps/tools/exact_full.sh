#!/usr/bin/env bash
# exact_full.sh <suite folder> [...] - the finished boundary runs of each folder under out/qual against all 4569 exact oracle rows (out/exp/exact/b1.boundary.exact2.jsonl, 8 s per root; the suite's own
# check uses the 2500-row snapshot b2500.exact.jsonl). Roots where the solver ran out of time are counted as unresolved and not judged. Prints one line per check; writes *_full.json and *_full.bad.tsv.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
EX="$W\\out\\exp\\exact\\b1.boundary.exact2.jsonl"
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
for q in "$@"; do
  QW="$W\\out\\qual\\$q"
  pin -Exe "$PY" -ArgLine "-I -B $WT\\exact_check.py $EX --root $QW\\root_boundary.out --json $QW\\root_boundary_full.json --list $QW\\root_boundary_full.bad.tsv" -Log "$QW\\root_boundary_full.log"
  echo "$q root exit $?: $(tail -1 "$J/out/qual/$q/root_boundary_full.log" | cut -c1-330)"
  pin -Exe "$PY" -ArgLine "-I -B $WT\\exact_check.py $EX --run $QW\\uci_boundary.jsonl --json $QW\\uci_boundary_full.json --list $QW\\uci_boundary_full.bad.tsv" -Log "$QW\\uci_boundary_full.log"
  echo "$q uci exit $?: $(tail -1 "$J/out/qual/$q/uci_boundary_full.log" | cut -c1-260)"
done
