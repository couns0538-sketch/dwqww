#!/usr/bin/env bash
# Check the honesty pins on a build, with the arm names read from the engine's
# own `uci` output rather than from this script.
#
# The four honesty pins quoted for the switch audit are bench 11, 13 and 16 plus
# perft 5. They are NOT the same set as the 11 documented pins in LOCK.md
# (5 depths x 2 net settings + perft 5) — both are pinned, and saying which set
# is meant is the whole point of printing it here.
#
# Exit non-zero if any pin moved.
set -euo pipefail

ENGINE=${1:?usage: check_pins.sh <engine>}
EXPECT_BENCH11=${EXPECT_BENCH11:-312866}
EXPECT_BENCH13=${EXPECT_BENCH13:-862329}
EXPECT_BENCH16=${EXPECT_BENCH16:-3024920}
EXPECT_PERFT5=${EXPECT_PERFT5:-4865609}

# One process per pin, so no pin borrows state from the previous one.
read_pin() {
  local out
  out=$(printf '%s\n' \
    'setoption name Threads value 1' \
    'setoption name Hash value 16' \
    'setoption name OwnBook value false' \
    'isready' \
    "$1" \
    'quit' | "$ENGINE" 2>&1) || true
  printf '%s\n' "$out"
}

fail=0
check_bench() {
  local depth=$1 expect=$2
  local got
  got=$(read_pin "bench $depth" | grep -oE 'nodes [0-9]+' | head -1 | awk '{print $2}')
  if [ "$got" = "$expect" ]; then
    printf 'bench %-2s nodes %s OK\n' "$depth" "$got"
  else
    printf 'bench %-2s nodes %s EXPECTED %s MISMATCH\n' "$depth" "${got:-none}" "$expect"
    fail=1
  fi
}

check_perft() {
  local got
  got=$(read_pin 'position startpos
go perft 5' | grep -oE '^nodes [0-9]+' | head -1 | awk '{print $2}')
  if [ "$got" = "$EXPECT_PERFT5" ]; then
    printf 'perft 5    nodes %s OK\n' "$got"
  else
    printf 'perft 5    nodes %s EXPECTED %s MISMATCH\n' "${got:-none}" "$EXPECT_PERFT5"
    fail=1
  fi
}

check_bench 11 "$EXPECT_BENCH11"
check_bench 13 "$EXPECT_BENCH13"
check_bench 16 "$EXPECT_BENCH16"
check_perft

if [ "$fail" -ne 0 ]; then
  echo "PINS MOVED"
  exit 1
fi
echo "all four honesty pins reproduce"
