#!/usr/bin/env bash
# honesty.sh: fresh process per command, no setoption. Raw engine stdout plus a .meta.
set -u
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$(cat ~/grok2_seat.txt)"
B=/agent/repos/base/forge-combo29/build/forge
P=/agent/repos/work/forge-combo29/build/forge

run_one() {
  local tag=$1 exe=$2 cmd=$3
  local out="$D/honesty_${tag}.txt"
  local meta="$D/honesty_${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$out"
  local sha id
  sha=$(sha256sum "$exe" | awk '{print $1}')
  id=$(printf 'uci\nquit\n' | "$exe" | awk -F'id name ' '/^id name /{print substr($0, 9); exit}')
  {
    echo "exe=$exe"
    echo "sha256=$sha"
    echo "id_name=$id"
    echo "options="
    echo "command=$cmd"
  } > "$meta"
  echo "==== $tag ===="
  cat "$out"
}

run_one B_bench11 "$B" "bench 11"
run_one B_bench13 "$B" "bench 13"
run_one B_bench16 "$B" "bench 16"
run_one B_perft5 "$B" "go perft 5"
run_one P_bench11 "$P" "bench 11"
run_one P_bench13 "$P" "bench 13"
run_one P_bench16 "$P" "bench 16"
run_one P_perft5 "$P" "go perft 5"
