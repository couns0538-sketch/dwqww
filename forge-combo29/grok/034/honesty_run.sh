#!/usr/bin/env bash
# Honesty check. One fresh process per line. No setoption.
# usage: honesty_run.sh EXE PREFIX
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="$1"
PREFIX="$2"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/$name.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id name $ID"
    echo "command=$cmd"
    echo "options:"
  } > "$DIR/$name.meta"
}
run_one "${PREFIX}_bench11" "bench 11"
run_one "${PREFIX}_bench13" "bench 13"
run_one "${PREFIX}_bench16" "bench 16"
run_one "${PREFIX}_perft5" "go perft 5"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id name $ID"
  for name in "${PREFIX}_bench11" "${PREFIX}_bench13" "${PREFIX}_bench16" "${PREFIX}_perft5"; do
    echo "===== $name ====="
    cat "$DIR/$name.txt"
  done
} > "$DIR/${PREFIX}.txt"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id name $ID"
  echo "command=bench 11; bench 13; bench 16; go perft 5"
  echo "options:"
} > "$DIR/${PREFIX}.meta"
echo "sha256=$SHA"
echo "id=$ID"
grep -H "nodes" "$DIR/${PREFIX}_bench11.txt" "$DIR/${PREFIX}_bench13.txt" "$DIR/${PREFIX}_bench16.txt"
grep -E "^nodes " "$DIR/${PREFIX}_perft5.txt"
