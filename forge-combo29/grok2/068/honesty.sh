#!/usr/bin/env bash
# honesty.sh <label> <exe> <outdir>
# One fresh process per line. No setoption. Raw stdout+stderr saved.
set -u
LABEL="$1"
EXE=$(readlink -f "$2")
OUT="$3"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print substr($0,9); exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  local raw="$OUT/honesty_${LABEL}_${name}.txt"
  local meta="$OUT/honesty_${LABEL}_${name}.meta"
  timeout 180 bash -c 'printf "%s\nquit\n" "$1" | "$2"' _ "$cmd" "$EXE" > "$raw" 2>&1
  local rc=$?
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id name $ID"
    echo "id_name_source separate process: uci then quit, same exe path"
    echo "options_sent none"
    echo "command $cmd"
    echo "exit $rc"
  } > "$meta"
  echo "$LABEL $name rc $rc"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
