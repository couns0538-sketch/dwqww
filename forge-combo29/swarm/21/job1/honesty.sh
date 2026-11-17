#!/usr/bin/env bash
# honesty.sh EXE OUTFILE : four honesty commands, fresh process each, raw output
set -u
EXE="$1"; OUT="$2"
: > "$OUT"
run() {
  local line="$1"
  {
    echo "=== CMD: $line"
    printf '%s\nquit\n' "$line" | "$EXE" 2>&1
    echo "=== END"
  } >> "$OUT"
}
run "uci"
run "bench 11"
run "bench 13"
run "bench 16"
run "go perft 5"
echo "EXE $EXE sha256 $(sha256sum "$EXE" | cut -d' ' -f1)" >> "$OUT"
