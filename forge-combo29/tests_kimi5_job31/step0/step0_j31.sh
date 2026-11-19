#!/bin/bash
# kimi5 job 31 step 0: fresh process per line, input logs kept.
set -u
EXE="$1"; OUT="$2"; mkdir -p "$OUT"
run_line () {
  local name="$1" opt="$2" cmd="$3"
  local inp="$OUT/${name}_input.log" out="$OUT/${name}.txt"
  {
    if [ -n "$opt" ]; then
      grep -v '^\s*#\|^\s*$' "$opt" | while read -r n v; do echo "setoption name $n value $v"; done
    fi
    echo "isready"; echo "ucinewgame"; echo "isready"; echo "$cmd"; echo "quit"
  } | tee "$inp" | "$EXE" > "$out" 2>&1
}
sha256sum "$EXE" | tee "$OUT/exe.sha256"
run_line none_bench11 "" "bench 11"
run_line none_bench13 "" "bench 13"
run_line none_perft5 "" "go perft 5"
run_line pc20_bench11 "/tmp/job31/pc20.opt" "bench 11"
run_line pc20_bench13 "/tmp/job31/pc20.opt" "bench 13"
for f in none_bench11 none_bench13 none_perft5 pc20_bench11 pc20_bench13; do
  printf '%-14s ' "$f"; grep -E "nodes" "$OUT/$f.txt" | tail -1
done
