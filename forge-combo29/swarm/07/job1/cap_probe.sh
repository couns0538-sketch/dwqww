#!/usr/bin/env bash
# cap_probe.sh EXE OUTDIR : feed FENs with many mobile pieces; count pseudo-legal/legal moves via perft 1
set -u
EXE="$1"; OUT="$2"; mkdir -p "$OUT"
i=0
while IFS='|' read -r name fen; do
  [ -z "${name:-}" ] && continue
  i=$((i+1))
  { echo uci; echo "setoption name Hash value 16"; echo "setoption name Threads value 1"; echo isready
    echo ucinewgame; echo isready
    echo "position fen $fen"
    echo isready
    echo "go perft 1"
    echo isready
    echo "go depth 4"
    echo isready
    echo quit; } > "$OUT/$name.in"
  timeout 120 "$EXE" < "$OUT/$name.in" > "$OUT/$name.out" 2> "$OUT/$name.err"
  rc=$?
  n=$(grep -c '^[a-h][1-8][a-h][1-8]' "$OUT/$name.out")
  echo "$name rc=$rc rootmoves=$n errlines=$(wc -l < "$OUT/$name.err")" | tee -a "$OUT/summary.txt"
done < "$3"
