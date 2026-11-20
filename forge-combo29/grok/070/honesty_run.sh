#!/usr/bin/env bash
# Honesty check. One fresh process per line. No setoption.
# usage: honesty_run.sh EXE TAG
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="$1"
TAG="$2"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDLINE=$(printf 'uci\nquit\n' | "$EXE" | grep '^id name ' | head -n 1)

run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$IDLINE"
    echo "options_sent=none"
    echo "command=$cmd"
  } > "$DIR/${name}.meta"
}

run_one "${TAG}_bench11" "bench 11"
run_one "${TAG}_bench13" "bench 13"
run_one "${TAG}_bench16" "bench 16"
run_one "${TAG}_perft5" "go perft 5"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$IDLINE"
  echo "---- bench 11 ----"
  cat "$DIR/${TAG}_bench11.txt"
  echo "---- bench 13 ----"
  cat "$DIR/${TAG}_bench13.txt"
  echo "---- bench 16 ----"
  cat "$DIR/${TAG}_bench16.txt"
  echo "---- perft 5 ----"
  cat "$DIR/${TAG}_perft5.txt"
} > "$DIR/${TAG}_HONESTY.txt"
echo "WROTE $DIR/${TAG}_HONESTY.txt"
grep -E 'bench depth|nodes ' "$DIR/${TAG}_HONESTY.txt"
