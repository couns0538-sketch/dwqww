#!/bin/bash
# kimi5 job 29 Step 0: the eight numbers of file 17 on the PC build
# (6b98f217 + pc_r15.patch sha256 d6bd72c5..., -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1,
#  g++ Release). A fresh engine process for every line; every command mirrored into an input log.
# usage: step0_j29.sh <engine> <outdir>
set -u
EXE="$1"; OUT="$2"; mkdir -p "$OUT"
JOB="$(cd "$(dirname "$0")" && pwd)"

run_line () {  # name optfile command...
  local name="$1" opt="$2" cmd="$3"
  local inp="$OUT/${name}_input.log" out="$OUT/${name}.txt"
  {
    if [ -n "$opt" ]; then
      grep -v '^\s*#\|^\s*$' "$opt" | while read -r n v; do echo "setoption name $n value $v"; done
    fi
    echo "isready"
    echo "ucinewgame"
    echo "isready"
    echo "$cmd"
    echo "quit"
  } | tee "$inp" | "$EXE" > "$out" 2>&1
}

sha256sum "$EXE" | tee "$OUT/exe.sha256"
printf 'uci\nquit\n' | tee "$OUT/uci_input.log" | "$EXE" > "$OUT/uci_list.txt" 2>&1

run_line none_bench11 "" "bench 11"
run_line none_bench13 "" "bench 13"
run_line none_bench16 "" "bench 16"
run_line none_perft5 "" "go perft 5"
run_line s14_bench11 "$JOB/s14.opt" "bench 11"
run_line s14_bench13 "$JOB/s14.opt" "bench 13"
run_line pc20_bench11 "$JOB/pc20.opt" "bench 11"
run_line pc20_bench13 "$JOB/pc20.opt" "bench 13"

echo "== results =="
for f in none_bench11 none_bench13 none_bench16 none_perft5 s14_bench11 s14_bench13 pc20_bench11 pc20_bench13; do
  printf '%-14s ' "$f"; grep -E "nodes" "$OUT/$f.txt" | tail -1
done
