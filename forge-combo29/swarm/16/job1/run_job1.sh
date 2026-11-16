#!/usr/bin/env bash
# run_job1.sh : full area-6 job-1 measurement (G 353 + R 500, plus controls)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
EXE="$HOME/builds/bld-release/forge"
mkdir -p "$HERE/raw"
python3 "$HERE/mirror_eval.py" "$EXE" "$HERE/set_G.epd" "$HERE/raw/G.tsv" "$HERE/raw/G.meta" | tee "$HERE/raw/G.summary"
python3 "$HERE/mirror_eval.py" "$EXE" "$HERE/set_R_seed1601.fens" "$HERE/raw/R.tsv" "$HERE/raw/R.meta" | tee "$HERE/raw/R.summary"
python3 "$HERE/mirror_eval.py" "$EXE" "$HERE/ctrl_same_twice.epd" "$HERE/raw/ctrl.tsv" "$HERE/raw/ctrl.meta" | tee "$HERE/raw/ctrl.summary"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$HERE/stamps.txt"
