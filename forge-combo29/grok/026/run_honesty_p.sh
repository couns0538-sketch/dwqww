#!/usr/bin/env bash
# Honesty check of exe P with no setoption. Four fresh processes.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/forge-p/forge
PY="$DIR/uci_harness.py"
python3 "$PY" honesty --exe "$EXE" --out "$DIR/honesty_p_bench11.txt" --send "bench 11"
python3 "$PY" honesty --exe "$EXE" --out "$DIR/honesty_p_bench13.txt" --send "bench 13"
python3 "$PY" honesty --exe "$EXE" --out "$DIR/honesty_p_bench16.txt" --send "bench 16"
python3 "$PY" honesty --exe "$EXE" --out "$DIR/honesty_p_perft5.txt" --send "go perft 5"
python3 "$DIR/collect_honesty_p.py"
