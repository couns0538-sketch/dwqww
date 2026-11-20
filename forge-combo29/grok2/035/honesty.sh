#!/usr/bin/env bash
# honesty.sh: fresh process per line, no setoption. Raw engine stdout in honesty_*.txt
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
B=/tmp/forge-b/forge
P=/tmp/forge-p/forge

idname() {
  printf 'uci\nquit\n' | "$1" | awk '/^id name /{print; exit}'
}

one() {
  local tag="$1" exe="$2" cmd="$3"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/honesty_${tag}.txt" 2>&1
  {
    echo "exe_path $exe"
    echo -n "sha256 "
    sha256sum "$exe"
    echo "id_line $(idname "$exe")"
    echo "options_sent none"
    echo "command $cmd"
    echo "fresh_process yes"
    echo "setoption_before no"
  } > "$D/honesty_${tag}.meta"
  echo "WROTE honesty_${tag}"
}

one B_bench11 "$B" "bench 11"
one B_bench13 "$B" "bench 13"
one B_bench16 "$B" "bench 16"
one B_perft5 "$B" "go perft 5"
one P_bench11 "$P" "bench 11"
one P_bench13 "$P" "bench 13"
one P_bench16 "$P" "bench 16"
one P_perft5 "$P" "go perft 5"

echo "----- signature lines -----"
for f in "$D"/honesty_*.txt; do
  echo "== $(basename "$f")"
  if [[ "$(basename "$f")" == *perft* ]]; then
    tail -n 1 "$f"
  else
    grep 'bench depth' "$f"
  fi
done
