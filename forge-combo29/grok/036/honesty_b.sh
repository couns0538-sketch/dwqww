#!/usr/bin/env bash
# Honesty check on exe B. Fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="${1:-/agent/repos/base/forge-combo29/build/forge}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local out="$DIR/${name}.txt"
  local meta="$DIR/${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id name $ID"
    echo "options none"
    echo "command $cmd"
  } > "$meta"
  echo "WROTE $out"
  cat "$out"
}
run_one honesty_b_bench11 "bench 11"
run_one honesty_b_bench13 "bench 13"
run_one honesty_b_bench16 "bench 16"
run_one honesty_b_perft5 "go perft 5"
