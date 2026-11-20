#!/usr/bin/env bash
# honesty.sh <exe> <tag> <outdir>
# Fresh process per line. No setoption. position startpos only before perft
# because the manual pin is "position startpos" then "go perft 5".
# After the measured command, "uci" is sent so the transcript holds "id name".
set -u
EXE=$1
TAG=$2
OUT=$3
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
run() {
  local name=$1
  shift
  local raw="$OUT/honesty_${TAG}_${name}.txt"
  local meta="$OUT/honesty_${TAG}_${name}.meta"
  printf '%s\n' "$@" "uci" "quit" | "$EXE" > "$raw"
  local id
  id=$(sed -n 's/^id name //p' "$raw" | head -n 1)
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id name ${id:-MISSING}"
    echo "options none"
    echo "commands ${*}"
  } > "$meta"
  echo "---- $TAG $name ----"
  grep -E 'bench depth|nodes ' "$raw" | tail -n 3
}
run bench11 "bench 11"
run bench13 "bench 13"
run bench16 "bench 16"
run perft5 "position startpos" "go perft 5"
