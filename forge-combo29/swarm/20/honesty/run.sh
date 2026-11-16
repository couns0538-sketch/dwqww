#!/usr/bin/env bash
# Seat 20 honesty check. One fresh engine process per line; raw output to files.
# usage: bash run.sh <exe> <outdir>
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
date -u +"start %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"
{
  echo "exe_started=$EXE"
  echo "sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
  echo "nm___asan_=$(nm -C "$EXE" 2>/dev/null | grep -c __asan_)"
  echo "nm___ubsan_=$(nm -C "$EXE" 2>/dev/null | grep -c __ubsan_)"
  echo "nm___tsan_=$(nm -C "$EXE" 2>/dev/null | grep -c __tsan_)"
  echo "cwd=$(pwd)"
  echo "host_nproc=$(nproc)"
  echo "gcc=$(${CXX:-g++} --version | head -1)"
  echo "--- uci answer (id name / option lines) ---"
  printf 'uci\nquit\n' | "$EXE" 2>&1
} > "$OUT/meta.txt" 2>&1
date -u +"meta %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"

run_one() { # name, stdin-text
  local name="$1"; local inp="$2"
  printf '%b' "$inp" > "$OUT/$name.stdin.txt"
  timeout 300 "$EXE" < "$OUT/$name.stdin.txt" > "$OUT/$name.out.txt" 2>&1
  echo "exit=$?" >> "$OUT/$name.out.txt"
  date -u +"$name %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"
}

run_one bench11 'bench 11\nquit\n'
run_one bench13 'bench 13\nquit\n'
run_one bench16 'bench 16\nquit\n'
run_one perft5 'position startpos\ngo perft 5\nquit\n'

{
  for n in bench11 bench13 bench16 perft5; do
    echo "== $n"
    grep -E 'Nodes searched|nodes|Nodes' "$OUT/$n.out.txt" | tail -3
    tail -1 "$OUT/$n.out.txt"
  done
} > "$OUT/summary.txt" 2>&1
date -u +"done %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"
cat "$OUT/summary.txt"
