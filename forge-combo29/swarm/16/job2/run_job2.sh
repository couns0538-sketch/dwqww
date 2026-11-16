#!/usr/bin/env bash
# run_job2.sh : area-6 job 2, left-right mirror over every no-castling G and R position
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
EXE="$HOME/builds/bld-release/forge"
mkdir -p "$HERE/raw"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$HERE/stamps.txt"
python3 "$HERE/mirror_lr.py" "$EXE" "$HERE/G_nocastle.fens" "$HERE/raw/G_lr.tsv" "$HERE/raw/G_lr.meta" \
  | tee "$HERE/raw/G_lr.summary"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$HERE/stamps.txt"
python3 "$HERE/mirror_lr.py" "$EXE" "$HERE/R_nocastle.fens" "$HERE/raw/R_lr.tsv" "$HERE/raw/R_lr.meta" \
  | tee "$HERE/raw/R_lr.summary"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$HERE/stamps.txt"
