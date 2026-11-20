#!/usr/bin/env bash
# Depth search. Extra UCI options are name=value arguments after the fixed ones.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=$1
FENS=$2
DEPTH=$3
OUT=$4
shift 4
OPTS=()
for item in "$@"; do
  OPTS+=(--opt "$item")
done
python3 "forge-combo29/grok/$S/uci_harness.py" search \
  --exe "$EXE" --fens "$FENS" --depth "$DEPTH" --out "$OUT" "${OPTS[@]}"
