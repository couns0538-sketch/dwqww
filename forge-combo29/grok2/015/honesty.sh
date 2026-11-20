#!/usr/bin/env bash
# honesty.sh: fresh process per line, no setoption. Raw stdout and a .meta beside it.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
B=/tmp/forge-base-build/forge
P=/tmp/forge-work-build/forge

run_one() {
  local tag="$1" exe="$2" cmd="$3"
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/${tag}.txt"
  {
    echo "exe: $exe"
    echo -n "sha256: "
    sha256sum "$exe"
    echo -n "id name: "
    printf 'uci\nquit\n' | "$exe" | awk '/^id name /{sub(/^id name /,""); print; exit}'
    echo "option lines sent:"
    echo "(none)"
    echo "stdin:"
    echo "$cmd"
    echo "quit"
    echo "note: id name is from a second process of the same exe that was sent only uci then quit. The measured process was sent only the stdin above."
  } > "$D/${tag}.meta"
  echo "wrote $tag"
}

run_one honesty_B_bench11 "$B" "bench 11"
run_one honesty_B_bench13 "$B" "bench 13"
run_one honesty_B_bench16 "$B" "bench 16"
run_one honesty_B_perft5 "$B" "go perft 5"
run_one honesty_P_bench11 "$P" "bench 11"
run_one honesty_P_bench13 "$P" "bench 13"
run_one honesty_P_bench16 "$P" "bench 16"
run_one honesty_P_perft5 "$P" "go perft 5"
echo HONESTY_DONE
