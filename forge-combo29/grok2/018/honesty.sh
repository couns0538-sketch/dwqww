#!/usr/bin/env bash
# honesty.sh EXE OUTDIR
# A fresh engine process for each line. No setoption.
set -u
EXE="$1"
OUT="$2"
mkdir -p "$OUT"
run_one() {
  local name="$1"
  shift
  printf '%s\nquit\n' "$*" | "$EXE" > "$OUT/$name.txt" 2>&1
}
run_one bench11 bench 11
run_one bench13 bench 13
run_one bench16 bench 16
run_one perft5 go perft 5
