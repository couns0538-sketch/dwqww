#!/usr/bin/env bash
# honesty.sh EXE LABEL OUTDIR
# One fresh process per line. No setoption. Command, then quit.
set -u
EXE="$1"
LABEL="$2"
OUT="$3"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk -F'\n' '/^id name /{print; exit}')
run_one() {
  local name="$1" cmd="$2"
  local raw="$OUT/honesty_${LABEL}_${name}.txt"
  local meta="$OUT/honesty_${LABEL}_${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$raw"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "$ID"
    echo "options none"
    echo "command $cmd"
    echo "note id name taken from a separate uci/quit process; this file's process received only the command then quit"
  } > "$meta"
  echo "WROTE $raw"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
