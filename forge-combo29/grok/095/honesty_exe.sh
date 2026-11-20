#!/usr/bin/env bash
# Honesty check. One fresh process per line. No setoption.
# usage: honesty_exe.sh EXE PREFIX
set -eu
EXE="$1"
PREFIX="$2"
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep -m1 '^id name ' || true)

run_one() {
  local tag="$1"
  local cmd="$2"
  local raw="$OUT/${PREFIX}_${tag}.txt"
  local meta="$OUT/${PREFIX}_${tag}.meta"
  printf 'uci\n%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options_sent=none"
    echo "command=$cmd"
    echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$meta"
  grep -E 'bench depth|^nodes ' "$raw" | tail -n 1
}

run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo HONESTY_DONE "$PREFIX"
