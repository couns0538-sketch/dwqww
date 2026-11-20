#!/usr/bin/env bash
# honesty.sh: one fresh engine process per line, no setoption.
# Raw stdout is the .txt; the .meta names that process's exe.
set -u
S=$(cat ~/grok2_seat.txt)
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$S"

idname() {
  printf 'uci\nquit\n' | "$1" | sed -n 's/^id name //p' | head -n 1
}

run_one() {
  local tag="$1" exe="$2" cmd="$3"
  local out="$D/honesty_${tag}.txt"
  local meta="$D/honesty_${tag}.meta"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$out"
  {
    echo "exe: $exe"
    echo "sha256: $(sha256sum "$exe" | awk '{print $1}')"
    echo "id_name: $(idname "$exe")"
    echo "id_name_source: separate process, command: uci"
    echo "honesty_process_options: (none)"
    echo "honesty_command: $cmd"
  } > "$meta"
  echo "=== $tag ==="
  grep -E 'bench depth |^nodes ' "$out" | tail -n 2
}

run_one B_bench11 /tmp/build-B/forge "bench 11"
run_one B_bench13 /tmp/build-B/forge "bench 13"
run_one B_bench16 /tmp/build-B/forge "bench 16"
run_one B_perft5 /tmp/build-B/forge "go perft 5"
run_one P_bench11 /tmp/build-P/forge "bench 11"
run_one P_bench13 /tmp/build-P/forge "bench 13"
run_one P_bench16 /tmp/build-P/forge "bench 16"
run_one P_perft5 /tmp/build-P/forge "go perft 5"
