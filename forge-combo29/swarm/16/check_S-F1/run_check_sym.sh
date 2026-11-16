#!/usr/bin/env bash
# run_check_sym.sh : S-F1 check, 4 configs x (G_353 + R_500 + Rbig_5000)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
EXE="$HOME/builds/bld-release/forge"
mkdir -p "$HERE/raw"
for cfg in default nonnue deadmat both; do
  date -u +%Y-%m-%dT%H:%M:%SZ >> "$HERE/stamps.txt"
  python3 "$HERE/check_sym.py" "$EXE" "$cfg" "$HERE/raw/${cfg}.tsv" \
      "$HERE/G_353.fens" "$HERE/R_500.fens" "$HERE/Rbig_5000.fens" \
      | tee "$HERE/raw/${cfg}.summary"
done
date -u +%Y-%m-%dT%H:%M:%SZ >> "$HERE/stamps.txt"
