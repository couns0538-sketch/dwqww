#!/usr/bin/env bash
# honesty.sh: fresh process per command, no setoption. Writes raw output and .meta beside it.
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
B=/tmp/forge-base/forge
P=/tmp/forge-work/forge

run_one() {
  exe=$1
  tag=$2
  cmd=$3
  out="$D/honesty_${tag}.txt"
  meta="$D/honesty_${tag}.meta"
  sha=$(sha256sum "$exe" | awk '{print $1}')
  idname=$(printf 'uci\nquit\n' | "$exe" | sed -n 's/^id name //p' | head -n 1)
  printf '%s\nquit\n' "$cmd" | "$exe" > "$out"
  {
    echo "exe $exe"
    echo "sha256 $sha"
    echo "id name $idname"
    echo "options none"
    echo "command $cmd"
  } > "$meta"
  echo "WROTE $tag"
}

run_one "$B" B_bench11 "bench 11"
run_one "$B" B_bench13 "bench 13"
run_one "$B" B_bench16 "bench 16"
run_one "$B" B_perft5 "go perft 5"
run_one "$P" P_bench11 "bench 11"
run_one "$P" P_bench13 "bench 13"
run_one "$P" P_bench16 "bench 16"
run_one "$P" P_perft5 "go perft 5"
echo DONE
