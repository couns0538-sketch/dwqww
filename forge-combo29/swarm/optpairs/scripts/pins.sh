#!/usr/bin/env bash
# Four honesty pins. bench N and perft must be sent on STDIN (argv `bench 11` prints
# nothing and exits 0). Each pin runs in a fresh process.
# Expected on 6b98f217 with the brief's g++ recipe:
#   bench 11 = 312,866   bench 13 = 862,329   bench 16 = 3,024,920   go perft 5 = 4,865,609
set -u
BIN=${1:-/tmp/build-optpairs/forge}
fail=0

pin_bench() {
  local d=$1 want=$2 got
  got=$(printf 'bench %s\nquit\n' "$d" | "$BIN" 2>&1 | sed -n 's/.*bench depth [0-9]* nodes \([0-9]*\) .*/\1/p')
  if [ "$got" = "$want" ]; then
    printf 'PIN bench %-2s OK   %s\n' "$d" "$got"
  else
    printf 'PIN bench %-2s FAIL got=%s want=%s\n' "$d" "${got:-<none>}" "$want"
    fail=1
  fi
}

pin_perft() {
  local want=$1 got
  got=$(printf 'position startpos\ngo perft 5\nquit\n' | "$BIN" 2>&1 | sed -n 's/^nodes \([0-9]*\)$/\1/p')
  if [ "$got" = "$want" ]; then
    printf 'PIN perft 5  OK   %s\n' "$got"
  else
    printf 'PIN perft 5  FAIL got=%s want=%s\n' "${got:-<none>}" "$want"
    fail=1
  fi
}

pin_bench 11 312866
pin_bench 13 862329
pin_bench 16 3024920
pin_perft 4865609

echo "PINS $([ $fail -eq 0 ] && echo MATCH || echo MISMATCH)"
exit $fail
