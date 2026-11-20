#!/usr/bin/env bash
# honesty.sh EXE OUTPREFIX
# A fresh engine process for each line. No setoption.
set -u
EXE="$1"
OUT="$2"
run() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "${OUT}_${name}.txt"
}
run bench11 "bench 11"
run bench13 "bench 13"
run bench16 "bench 16"
run perft5 "go perft 5"
echo "honesty done $OUT"
