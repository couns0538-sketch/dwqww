#!/usr/bin/env bash
# honesty.sh: one fresh process per command, no setoption. Raw stdout saved beside a .meta.
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
B=/agent/repos/base/forge-combo29/build/forge
P=/agent/repos/work/forge-combo29/build/forge

idname() {
  printf 'uci\nquit\n' | "$1" | awk -F'id name ' '/^id name /{print $2; exit}'
}

run_one() {
  local tag=$1 exe=$2 cmd=$3
  local out="$D/honesty_${tag}.txt"
  local meta="$D/honesty_${tag}.meta"
  printf '%s\n' "$cmd" | "$exe" > "$out"
  {
    echo "exe=$exe"
    echo -n "sha256="
    sha256sum "$exe" | awk '{print $1}'
    echo "id_name=$(idname "$exe")"
    echo "command=$cmd"
    echo "options=(none)"
  } > "$meta"
  echo "WROTE $out"
}

run_one B_bench11 "$B" "bench 11"
run_one B_bench13 "$B" "bench 13"
run_one B_bench16 "$B" "bench 16"
run_one B_perft5 "$B" "go perft 5"
run_one P_bench11 "$P" "bench 11"
run_one P_bench13 "$P" "bench 13"
run_one P_bench16 "$P" "bench 16"
run_one P_perft5 "$P" "go perft 5"

echo "---- nodes ----"
for f in "$D"/honesty_*.txt; do
  echo -n "$(basename "$f"): "
  grep -E 'nodes |^nodes ' "$f" | tail -n 1
done
