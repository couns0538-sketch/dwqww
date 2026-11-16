#!/usr/bin/env bash
# honesty.sh — STEP 2 honesty check for swarm seat 28 (area 8).
# Each line is a FRESH engine process; raw output saved as text files.
set -u
EXE=${EXE:-$HOME/build/base-release/forge}
OUT=${OUT:?need OUT dir}
mkdir -p "$OUT"
for spec in "bench11:bench 11" "bench13:bench 13" "bench16:bench 16" "perft5:go perft 5"; do
  name=${spec%%:*}
  cmd=${spec#*:}
  printf 'ucinewgame\n%s\nquit\n' "$cmd" | "$EXE" > "$OUT/$name.txt" 2>&1
  echo "$name rc=$?" >> "$OUT/rc.txt"
done
shasum -a 256 "$EXE" > "$OUT/exe.sha256"
echo "id name" > "$OUT/idname.txt"
printf 'uci\nquit\n' | "$EXE" 2>&1 | grep -m1 '^id name' >> "$OUT/idname.txt"
cat "$OUT/bench11.txt" "$OUT/bench13.txt" "$OUT/bench16.txt" "$OUT/perft5.txt" | grep -E 'nodes|perft'
