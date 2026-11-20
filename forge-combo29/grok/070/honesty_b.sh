#!/usr/bin/env bash
# Honesty check of exe B. One fresh process per line. No setoption.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/tmp/forge-base/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -n 1)

run_one() {
  local name="$1"
  local cmd="$2"
  local out="$DIR/${name}.txt"
  local meta="$DIR/${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$meta"
}

run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"

{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$IDLINE"
  echo "---- bench 11 ----"
  cat "$DIR/honesty_b_bench11.txt"
  echo "---- bench 13 ----"
  cat "$DIR/honesty_b_bench13.txt"
  echo "---- bench 16 ----"
  cat "$DIR/honesty_b_bench16.txt"
  echo "---- perft 5 ----"
  cat "$DIR/honesty_b_perft5.txt"
} > "$DIR/HONESTY_B.txt"

echo "WROTE $DIR/HONESTY_B.txt"
grep -E 'nodes|bench' "$DIR/HONESTY_B.txt" | tail -n 20
