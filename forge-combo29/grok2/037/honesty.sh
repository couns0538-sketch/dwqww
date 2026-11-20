#!/usr/bin/env bash
# honesty.sh: one fresh process per command, no setoption. Writes raw output and a .meta beside it.
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"
B=/agent/repos/base/forge-combo29/build/forge
P=/agent/repos/work/forge-combo29/build/forge

id_of() {
  printf 'uci\nquit\n' | "$1" | awk '/^id name /{sub(/^id name /,""); print; exit}'
}

run_one() {
  local tag="$1" exe="$2" cmd="$3"
  local out="$D/${tag}.txt" meta="$D/${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$out"
  {
    echo "exe: $exe"
    echo "sha256: $(sha256sum "$exe" | awk '{print $1}')"
    echo "id name: $(id_of "$exe")"
    echo "options sent: none"
    echo "command: $cmd"
    echo "started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$meta"
  echo "WROTE $tag"
}

run_one honesty_B_bench11 "$B" "bench 11"
run_one honesty_B_bench13 "$B" "bench 13"
run_one honesty_B_bench16 "$B" "bench 16"
run_one honesty_B_perft5  "$B" "go perft 5"
run_one honesty_P_bench11 "$P" "bench 11"
run_one honesty_P_bench13 "$P" "bench 13"
run_one honesty_P_bench16 "$P" "bench 16"
run_one honesty_P_perft5  "$P" "go perft 5"

echo "---- nodes ----"
for f in honesty_B_bench11 honesty_B_bench13 honesty_B_bench16 honesty_B_perft5 honesty_P_bench11 honesty_P_bench13 honesty_P_bench16 honesty_P_perft5; do
  echo -n "$f: "
  grep -E 'nodes |bench depth' "$D/$f.txt" | tail -n 1
done
