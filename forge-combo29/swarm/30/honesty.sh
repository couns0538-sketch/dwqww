#!/usr/bin/env bash
# honesty check: fresh engine process per line, raw output kept
set -u
EXE=${1:?exe}
OUT=${2:?outdir}
mkdir -p "$OUT"
sha256sum "$EXE" > "$OUT/exe.sha256"
{
  echo "exe: $(readlink -f "$EXE")"
  sha256sum "$EXE"
  printf 'uci\nisready\nquit\n' | "$EXE" 2>&1 | grep -E '^id name|^id author'
  echo "--- nm -C $(basename "$EXE") | grep -c __asan_ = $(nm -C "$EXE" 2>/dev/null | grep -c __asan_)"
  echo "--- nm -C $(basename "$EXE") | grep -c __ubsan_ = $(nm -C "$EXE" 2>/dev/null | grep -c __ubsan_)"
  date -u
} > "$OUT/meta.txt"

run() { # name, commands
  local name=$1; shift
  printf '%s\n' "$@" | "$EXE" 2>&1 > "$OUT/$name.raw"
  date -u >> "$OUT/stamps.txt"
  echo "$name: $(grep -E 'nodes|Nodes' "$OUT/$name.raw" | tail -1)"
}

run bench11 'uci' 'isready' 'bench 11' 'quit'
run bench13 'uci' 'isready' 'bench 13' 'quit'
run bench16 'uci' 'isready' 'bench 16' 'quit'
run perft5 'uci' 'isready' 'position startpos' 'go perft 5' 'quit'
