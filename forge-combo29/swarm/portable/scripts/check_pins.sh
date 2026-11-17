#!/usr/bin/env bash
# The gate: the native build must reproduce the lock pins BEFORE any other
# build is compared to it. If this fails, every ratio downstream is measured
# against the wrong baseline.
#
# Pins from LOCK.md (Threads 1, Hash 16, OwnBook false):
#   net on : 312866 / 862329 / 3024920 / 12389307 / 34048354  (depths 11/13/16/20/22)
#   net off: 375354 / 907205 / 2448617 / 13573040 / 24506465
#   perft 5 startpos: 4865609
set -uo pipefail
EXE="${1:-/tmp/build/native/forge}"
DEEP="${DEEP:-0}"   # DEEP=1 adds the depth-20/22 pins (slow)

want_on_short="312866 862329 3024920"
want_off_short="375354 907205 2448617"
want_on_full="312866 862329 3024920 12389307 34048354"
want_off_full="375354 907205 2448617 13573040 24506465"
want_perft="4865609"

depths="11 13 16"
[ "${DEEP}" = "1" ] && depths="11 13 16 20 22"

out=$(mktemp)
{
  echo "setoption name OwnBook value false"
  for d in $depths; do echo "bench $d"; done
  echo "setoption name UseNNUE value false"
  for d in $depths; do echo "bench $d"; done
  echo "setoption name UseNNUE value true"
  echo "position startpos"
  echo "go perft 5"
} | "$EXE" > "$out" 2>&1

mapfile -t got < <(awk '/info string bench depth/{for(i=1;i<=NF;i++) if($i=="nodes") print $(i+1)}' "$out")
perft=$(awk '/^nodes /{print $2}' "$out" | tail -1)
# Count the DEPTHS, not the characters of the depth string: `set -- $depths` is the
# only form that gives the right n for both "11 13 16" and "11 13 16 20 22".
set -- $depths
n=$#

on_got="${got[*]:0:$n}"
off_got="${got[*]:$n:$n}"
if [ "${DEEP}" = "1" ]; then want_on="$want_on_full"; want_off="$want_off_full"
else want_on="$want_on_short"; want_off="$want_off_short"; fi

echo "net-on : $on_got"
echo "net-off: $off_got"
echo "perft5 : $perft"

status=0
[ "$on_got" = "$want_on" ]   || { echo "MISMATCH net-on  (want $want_on)";   status=1; }
[ "$off_got" = "$want_off" ] || { echo "MISMATCH net-off (want $want_off)"; status=1; }
[ "$perft" = "$want_perft" ] || { echo "MISMATCH perft5  (want $want_perft)"; status=1; }

if [ $status -eq 0 ]; then
  echo "PINS MATCH combo29 (depths: $depths)"
else
  echo "PIN MISMATCH -- baseline is not established; do not compare builds to it"
fi
rm -f "$out"
exit $status
