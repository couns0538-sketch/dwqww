#!/usr/bin/env bash
# honesty.sh: fresh process per line, no setoption. Raw stdout only.
set -u
B=/agent/repos/base/forge-combo29/build/forge
P=/agent/repos/work/forge-combo29/build/forge
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"

one() {
  local exe="$1" tag="$2" cmd="$3"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/honesty_${tag}.txt"
  local id
  id=$(printf 'uci\nquit\n' | "$exe" | sed -n 's/^id name //p' | head -n 1)
  {
    echo "exe: $exe"
    echo "sha256: $(sha256sum "$exe" | awk '{print $1}')"
    echo "id name: $id"
    echo "command: $cmd"
    echo "options: none"
    echo "note: measured process received only the command and quit; id name is from a second process of the same exe that received only uci and quit"
  } > "$D/honesty_${tag}.meta"
  echo "WROTE honesty_${tag}.txt"
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
