#!/usr/bin/env bash
# honesty_patch.sh EXE OUTFILE : the four honesty commands, fresh process each
set -u
EXE="$1"; OUT="$2"
: > "$OUT"
for c in "bench 11" "bench 13" "bench 16" "go perft 5"; do
  echo "=== CMD: $c" >> "$OUT"
  printf '%s\nquit\n' "$c" | "$EXE" 2>&1 | grep -E 'bench depth|^nodes ' >> "$OUT"
done
echo "=== sha256 $(sha256sum "$EXE" | cut -d' ' -f1)" >> "$OUT"
cat "$OUT"