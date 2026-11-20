#!/usr/bin/env bash
# Honesty check: fresh process per line, no setoption. Raw engine stdout only.
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
B=/agent/repos/base/forge-combo29/build/forge
P=/agent/repos/work/forge-combo29/build/forge

idname() {
  printf 'uci\nquit\n' | "$1" | awk -F'id name ' '/^id name /{print $2; exit}'
}

one() {
  local tag="$1" exe="$2" cmd="$3"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/${tag}.txt"
  {
    echo "exe $exe"
    sha256sum "$exe"
    echo "id name $(idname "$exe")"
    echo "options sent: none"
    echo "command: $cmd"
  } > "$D/${tag}.meta"
  echo "$tag $(grep -E 'nodes ' "$D/${tag}.txt" | tail -n 1)"
}

one honesty_B_bench11 "$B" "bench 11"
one honesty_B_bench13 "$B" "bench 13"
one honesty_B_bench16 "$B" "bench 16"
one honesty_B_perft5 "$B" "go perft 5"
one honesty_P_bench11 "$P" "bench 11"
one honesty_P_bench13 "$P" "bench 13"
one honesty_P_bench16 "$P" "bench 16"
one honesty_P_perft5 "$P" "go perft 5"
