#!/usr/bin/env bash
# honesty.sh: fresh process per line, no setoption. Raw output next to this script.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
run_one() {
  local tag="$1" exe="$2" cmd="$3" out="$4"
  local sha idname
  sha=$(sha256sum "$exe" | awk '{print $1}')
  idname=$(printf 'uci\nquit\n' | "$exe" | awk -F'id name ' '/^id name /{print $2; exit}')
  printf '%s\nquit\n' "$cmd" | "$exe" > "$D/$out"
  {
    echo "exe: $exe"
    echo "sha256: $sha"
    echo "id_name: $idname"
    echo "options: (none)"
    echo "command: $cmd"
  } > "$D/${out%.txt}.meta"
  echo "WROTE $out"
}
B=/home/ubuntu/build-b/forge
P=/home/ubuntu/build-p/forge
run_one B "$B" "bench 11" honesty_B_bench11.txt
run_one B "$B" "bench 13" honesty_B_bench13.txt
run_one B "$B" "bench 16" honesty_B_bench16.txt
run_one B "$B" "go perft 5" honesty_B_perft5.txt
run_one P "$P" "bench 11" honesty_P_bench11.txt
run_one P "$P" "bench 13" honesty_P_bench13.txt
run_one P "$P" "bench 16" honesty_P_bench16.txt
run_one P "$P" "go perft 5" honesty_P_perft5.txt
echo "---- nodes ----"
grep -H -E 'nodes ' "$D"/honesty_*.txt
