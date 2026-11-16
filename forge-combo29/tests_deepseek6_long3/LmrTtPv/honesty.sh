#!/usr/bin/env bash
# Honesty check: one fresh engine process per line, raw output to its own file.
set -u
EXE="${1:?exe path}"
OUT="${2:-.}"
n=0
for d in 11 13 16; do
  n=$((n+1))
  f="$OUT/honesty_bench${d}.txt"
  printf 'bench %s\nquit\n' "$d" | "$EXE" > "$f" 2>&1
done
f="$OUT/honesty_perft5.txt"
printf 'position startpos\ngo perft 5\nquit\n' | "$EXE" > "$f" 2>&1
echo "wrote honesty_bench11/13/16.txt and honesty_perft5.txt in $OUT"
