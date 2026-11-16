#!/usr/bin/env bash
# honesty.sh <exe> <outdir> : four honesty numbers, one fresh engine process per line.
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
{
  echo "exe started: $EXE"
  sha256sum "$EXE"
  echo "--- uci id ---"
  printf 'uci\nquit\n' | "$EXE" | grep '^id name'
} > "$OUT/meta.txt" 2>&1
for spec in "bench 11" "bench 13" "bench 16" "go perft 5"; do
  tag=$(echo "$spec" | tr ' ' '_')
  printf 'ucinewgame\nisready\n%s\nquit\n' "$spec" | "$EXE" > "$OUT/$tag.raw" 2>&1
  n=$(grep -oE 'nodes[[:space:]]+[0-9]+' "$OUT/$tag.raw" | tail -1 | grep -oE '[0-9]+')
  [ -n "${n:-}" ] || n=$(grep -oE '^[0-9]+$' "$OUT/$tag.raw" | tail -1)
  echo "$spec -> ${n:-NONE}"
done
