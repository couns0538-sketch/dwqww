#!/usr/bin/env bash
# Honesty check on the plain engine. One fresh process per line. No setoption.
set -u
EXE=/agent/repos/base/forge-combo29/build/forge
OUT="$(cd "$(dirname "$0")" && pwd)"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
run_one() {
  local name="$1"
  local cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${name}.txt"
  {
    echo "exe=$EXE"
    echo "sha256=$SHA"
    echo "id_name=$ID"
    echo "options=none"
    echo "command=$cmd"
  } > "$OUT/${name}.meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
python3 "$OUT/write_honesty_b.py"
