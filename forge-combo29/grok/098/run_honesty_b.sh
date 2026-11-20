#!/usr/bin/env bash
# Honesty check of exe B. Fresh process per line. No setoption.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="/agent/repos/base/forge-combo29/build-release/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')

printf 'uci\nquit\n' | "$EXE" > "$DIR/honesty_b_uci.txt"
ID=$(sed -n 's/^id name //p' "$DIR/honesty_b_uci.txt" | head -1)

run_one() {
  local tag="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/${tag}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$ID"
    echo "options_sent=none"
    echo "command=$cmd"
    echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$DIR/${tag}.meta"
}

run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"

nodes_of() {
  grep -oE 'nodes [0-9]+' "$1" | awk '{print $2}' | tail -1
}

b11=$(nodes_of "$DIR/honesty_b_bench11.txt")
b13=$(nodes_of "$DIR/honesty_b_bench13.txt")
b16=$(nodes_of "$DIR/honesty_b_bench16.txt")
p5=$(nodes_of "$DIR/honesty_b_perft5.txt")

{
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$ID"
  echo "bench11_nodes=$b11 expected=312866"
  echo "bench13_nodes=$b13 expected=862329"
  echo "bench16_nodes=$b16 expected=3024920"
  echo "perft5_nodes=$p5 expected=4865609"
  if [ "$b11" = 312866 ] && [ "$b13" = 862329 ] && [ "$b16" = 3024920 ] && [ "$p5" = 4865609 ]; then
    echo "result=PASS"
  else
    echo "result=FAIL"
  fi
  echo
  echo "===== honesty_b_bench11.txt ====="
  cat "$DIR/honesty_b_bench11.txt"
  echo "===== honesty_b_bench13.txt ====="
  cat "$DIR/honesty_b_bench13.txt"
  echo "===== honesty_b_bench16.txt ====="
  cat "$DIR/honesty_b_bench16.txt"
  echo "===== honesty_b_perft5.txt ====="
  cat "$DIR/honesty_b_perft5.txt"
} > "$DIR/HONESTY_B.txt"

echo "WROTE $DIR/HONESTY_B.txt"
tail -n 8 "$DIR/HONESTY_B.txt" | head -n 8
grep '^result=' "$DIR/HONESTY_B.txt"
