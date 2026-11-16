#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : the four honesty numbers, each a FRESH process, raw output saved.
set -u
EXE="$1"; OUT="$2"
mkdir -p "$OUT"
run() { # name, uci lines
  local name="$1"; shift
  printf '%s\n' "$@" | "$EXE" > "$OUT/$name.raw" 2>&1
  grep -E 'nodes|Nodes searched' "$OUT/$name.raw" | tail -n 2 > "$OUT/$name.nodes"
}
run bench11 'uci' 'bench 11' 'quit'
run bench13 'uci' 'bench 13' 'quit'
run bench16 'uci' 'bench 16' 'quit'
run perft5  'uci' 'position startpos' 'go perft 5' 'quit'
for f in bench11 bench13 bench16 perft5; do
  echo "== $f"; cat "$OUT/$f.nodes"
done
