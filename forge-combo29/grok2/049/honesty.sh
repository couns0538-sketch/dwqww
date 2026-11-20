#!/usr/bin/env bash
# honesty.sh: one fresh engine process per line, no setoption.
set -u
B=/tmp/forge-base-build/forge
P=/tmp/forge-work-build/forge
D="$(cd "$(dirname "$0")" && pwd)"
one() {
  local exe="$1" tag="$2" cmd="$3"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/honesty_${tag}.txt"
}
one "$B" B_bench11 "bench 11"
one "$B" B_bench13 "bench 13"
one "$B" B_bench16 "bench 16"
one "$B" B_perft5 "go perft 5"
one "$P" P_bench11 "bench 11"
one "$P" P_bench13 "bench 13"
one "$P" P_bench16 "bench 16"
one "$P" P_perft5 "go perft 5"
echo HONESTY_DONE
grep -H "nodes" "$D"/honesty_*.txt
