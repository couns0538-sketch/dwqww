#!/usr/bin/env bash
# Usage: scripts/check_pins.sh [path/to/forge]   (default build/forge)
# Checks the combo29 lock bench pins (net on + net off) and startpos perft 5.
set -euo pipefail
exe="${1:-build/forge}"
want_on="312866 862329 3024920 12389307 34048354"
want_off="375354 907205 2448617 13573040 24506465"
want_perft="4865609"
{
  echo "setoption name UseNNUE value true"; for d in 11 13 16 20 22; do echo "bench $d"; done
  echo "setoption name UseNNUE value false"; for d in 11 13 16 20 22; do echo "bench $d"; done
  echo "position startpos"; echo "go perft 5"; sleep 1; echo "quit"
} | "$exe" > pins_out.txt
got=$(awk '/info string bench depth/{for(i=1;i<=NF;i++) if($i=="nodes") printf "%s ", $(i+1)}' pins_out.txt)
got_on=$(echo $got | cut -d' ' -f1-5); got_off=$(echo $got | cut -d' ' -f6-10)
got_perft=$(awk '/^nodes /{print $2}' pins_out.txt | tail -1)
echo "net-on : $got_on"; echo "net-off: $got_off"; echo "perft5 : $got_perft"
if [[ "$got_on" == "$want_on" && "$got_off" == "$want_off" && "$got_perft" == "$want_perft" ]]; then
  echo "PINS MATCH combo29"; else echo "PIN MISMATCH (want on: $want_on / off: $want_off / perft5: $want_perft)"; exit 1; fi
