#!/usr/bin/env bash
# honesty.sh : build identity + four known numbers, one fresh engine process per line.
# Run from the repo working tree root. Raw output -> job0/raw/.
set -u
EXE="${1:-$HOME/build/forge}"
OUT="$2"
mkdir -p "$OUT"
{
  echo "exe_started=$EXE"
  sha256sum "$EXE"
  echo "gcc=$(g++ --version | head -1)"
  echo "uname=$(uname -a)"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/meta.txt"

run_one() { # name, commands
  local name="$1"; shift
  printf '%s\n' "$@" | "$EXE" > "$OUT/$name.out" 2> "$OUT/$name.err"
  echo "exit=$? name=$name" >> "$OUT/exits.txt"
}

: > "$OUT/exits.txt"

# bench 11/13/16
for d in 11 13 16; do
  run_one "bench$d" "uci" "isready" "bench $d" "quit"
done
# go perft 5 from startpos (with ucinewgame + isready first)
run_one "perft5" "uci" "ucinewgame" "isready" "position startpos" "go perft 5" "quit"

# print the numbers
for f in bench11 bench13 bench16 perft5; do
  echo "== $f"
  grep -E "nodes|Nodes" "$OUT/$f.out" | tail -3
done
