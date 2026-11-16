#!/usr/bin/env bash
# honesty.sh EXE OUTDIR : fresh process per line, raw output saved
set -u
EXE="$1"; OUT="$2"
mkdir -p "$OUT"
run_one() {
  name="$1"; shift
  { printf 'uci\n'; printf 'setoption name Hash value 16\n'; printf 'setoption name Threads value 1\n';
    printf 'isready\n'; printf 'ucinewgame\n'; printf 'isready\n'; printf '%s\n' "$@"; printf 'quit\n'; } > "$OUT/$name.in"
  "$EXE" < "$OUT/$name.in" > "$OUT/$name.out" 2> "$OUT/$name.err"
  echo "== $name exit=$?" >> "$OUT/summary.txt"
  grep -E '^(info|bestmove|readyok|id )' "$OUT/$name.out" | tail -3 >> "$OUT/summary.txt"
  grep -oE 'nodes [0-9]+' "$OUT/$name.out" | tail -1 >> "$OUT/summary.txt"
}
: > "$OUT/summary.txt"
sha256sum "$EXE" >> "$OUT/summary.txt"
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
echo "--- summary ---"; cat "$OUT/summary.txt"
