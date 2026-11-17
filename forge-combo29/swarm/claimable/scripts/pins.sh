#!/usr/bin/env bash
# Usage: pins.sh EXE OUTDIR LABEL
set -uo pipefail
exe="$1"; out="$2"; label="$3"
mkdir -p "$out"
{
  echo "uci"
  echo "setoption name UseNNUE value true"; for d in 11 13 16 20 22; do echo "bench $d"; done
  echo "setoption name UseNNUE value false"; for d in 11 13 16 20 22; do echo "bench $d"; done
  echo "position startpos"; echo "go perft 5"; sleep 2; echo "quit"
} | timeout 1800 "$exe" > "$out/pins.raw.txt" 2> "$out/pins.stderr.txt"
echo "exit=$?" > "$out/pins.meta"
echo "exe=$exe" >> "$out/pins.meta"
echo "label=$label" >> "$out/pins.meta"
sha256sum "$exe" >> "$out/pins.meta"
awk '/info string bench depth/{for(i=1;i<=NF;i++) if($i=="nodes") printf "%s ", $(i+1)} END{print ""}' "$out/pins.raw.txt"
awk '/^nodes /{print $2}' "$out/pins.raw.txt" | tail -1
