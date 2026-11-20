#!/usr/bin/env bash
# Fresh process per line. No setoption. quit is sent only so the process exits.
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
B="$HOME/build-base/forge"
P="$HOME/build-work/forge"
run_one() {
  local exe="$1" name="$2" cmd="$3"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/${name}.txt" 2>&1
  echo "wrote ${name}.txt"
}
run_one "$B" honesty_B_bench11 "bench 11"
run_one "$B" honesty_B_bench13 "bench 13"
run_one "$B" honesty_B_bench16 "bench 16"
run_one "$B" honesty_B_perft5 "go perft 5"
run_one "$P" honesty_P_bench11 "bench 11"
run_one "$P" honesty_P_bench13 "bench 13"
run_one "$P" honesty_P_bench16 "bench 16"
run_one "$P" honesty_P_perft5 "go perft 5"
