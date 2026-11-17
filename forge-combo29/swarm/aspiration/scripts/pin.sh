#!/bin/bash
# The four honesty pins. Nothing is recorded from a build that fails these.
#
# Two traps this avoids:
#   * `bench N` must arrive on STDIN. `./forge bench 11` as argv prints NOTHING
#     and exits 0 -- a silent way to record no number.
#   * `OwnBook` defaults to true. With the book on, bench 11 reads 1,919,423, a
#     plausible-looking wrong number. Every pin sets it false.
# The bench line is `... nodes <n> time <t> nps <r>`; the token after `nodes` is
# taken explicitly, because grabbing the LAST field yields `nps` instead.
set -u
B=${1:?usage: pin.sh <path-to-forge>}

fail=0
expect() { # name got want
  if [ "$2" = "$3" ]; then
    printf '%-10s %10s  OK\n' "$1" "$2"
  else
    printf '%-10s %10s  MISMATCH (want %s)\n' "$1" "${2:-NONE}" "$3"
    fail=1
  fi
}

for n in 11 13 16; do
  out=$(printf 'uci\nsetoption name OwnBook value false\nisready\nbench %s\nquit\n' "$n" | "$B" 2>&1)
  nodes=$(printf '%s\n' "$out" | awk -v d="$n" '
    $0 ~ ("info string bench depth " d " nodes ") {
      for (i = 1; i <= NF; i++) if ($i == "nodes") { print $(i + 1); exit }
    }')
  case $n in
    11) expect "bench 11" "$nodes" 312866 ;;
    13) expect "bench 13" "$nodes" 862329 ;;
    16) expect "bench 16" "$nodes" 3024920 ;;
  esac
done

out=$(printf 'uci\nsetoption name OwnBook value false\nisready\nposition startpos\ngo perft 5\nquit\n' | "$B" 2>&1)
perft=$(printf '%s\n' "$out" | awk '$1 == "nodes" { print $2; exit }')
expect "perft 5" "$perft" 4865609

exit $fail
