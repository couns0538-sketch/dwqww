#!/usr/bin/env bash
# Honesty check of exe P. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE="/agent/repos/work/forge-combo29/build/forge"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')

run_one() {
  local name="$1"
  local cmds="$2"
  local raw="$OUT/${name}.txt"
  local meta="$OUT/${name}.meta"
  printf '%s\nquit\n' "$cmds" | "$EXE" > "$raw"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "id name $ID"
    echo "command:"
    printf '%s\n' "$cmds"
    echo "options: none"
  } > "$meta"
}

run_one honesty_p_bench11 "bench 11"
run_one honesty_p_bench13 "bench 13"
run_one honesty_p_bench16 "bench 16"
run_one honesty_p_perft5 "go perft 5"

{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "id name $ID"
  echo "options: none"
  echo "---- bench 11 ----"
  cat "$OUT/honesty_p_bench11.txt"
  echo "---- bench 13 ----"
  cat "$OUT/honesty_p_bench13.txt"
  echo "---- bench 16 ----"
  cat "$OUT/honesty_p_bench16.txt"
  echo "---- perft 5 ----"
  cat "$OUT/honesty_p_perft5.txt"
} > "$OUT/HONESTY_P.txt"
