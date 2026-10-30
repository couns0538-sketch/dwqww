#!/bin/bash
# R9: copy the small evidence files of the SPSA runs from scratch into opus_r9/runs/<run>/ (PGNs stay in scratch)
# and print one status line per run. usage: snapshot_runs.sh <worktree root> <runs dir> <run> [<run> ...]
ROOT=$1; RUNS=$2; shift 2
for r in "$@"; do
  src="$RUNS/$r"; dst="$ROOT/opus_r9/runs/$r"
  [ -d "$src" ] || continue
  mkdir -p "$dst"
  for f in config.json tuner.log history.csv iterations.jsonl governor_changes.jsonl; do
    [ -f "$src/$f" ] && cp "$src/$f" "$dst/$f"
  done
  n=$(grep -c '"batch"' "$src/iterations.jsonl" 2>/dev/null || echo 0)
  last=$(grep -E "batch [0-9]+:|governor|stop:|end:" "$src/tuner.log" | tail -1 | cut -c1-200)
  echo "$r: $n batches; $last"
done
