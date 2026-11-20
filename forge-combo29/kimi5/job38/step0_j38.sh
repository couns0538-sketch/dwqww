#!/bin/bash
# kimi5 job 38 Step 0: the eight numbers of file 30 (file 17's pins) on the plain build
# (6b98f217 + pc_r15 + MATE_ALPHA_GUARD), then the twelve cells of K7 (PC20 = pc20_all1024.opt).
# A fresh engine process for every line; every command mirrored into an input log.
# usage: step0_j38.sh <engine> <outdir> <jobdir>
set -u
EXE="$1"; OUT="$2"; JOB="$3"; mkdir -p "$OUT"

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

run_line none_bench11 "" "bench 11"
run_line none_bench13 "" "bench 13"
run_line none_bench16 "" "bench 16"
run_line none_perft5 "" "go perft 5"
run_line s14_bench11 "$JOB/s14.opt" "bench 11"
run_line s14_bench13 "$JOB/s14.opt" "bench 13"
run_line pc20_bench11 "$JOB/pc20.opt" "bench 11"
run_line pc20_bench13 "$JOB/pc20.opt" "bench 13"

# ---- K7: four positions x three go depth 8 forms, PC20 (pc20_all1024.opt) ----
P1="startpos"
F2="rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1"
F3="1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
F4="8/3b4/8/1p1pk2p/7P/P1B1KP1P/1Pr1N3/8 b - - 0 1"
ALL1="a2a3 b2b3 c2c3 d2d3 e2e3 f2f3 g2g3 h2h3 a2a4 b2b4 c2c4 d2d4 e2e4 f2f4 g2g4 h2h4 b1a3 b1c3 g1f3 g1h3"
ALL2="g1e2 c3e2 c3e4 f1e2 d1e2"
ALL3="d5d4 e5e4 g7g6 g7g5 f6e4 f6g4 f6d7 f6h7 f6e8 f6g8 f5b1 f5c2 f5d3 f5h3 f5e4 f5g4 f5e6 f5g6 f5d7 f5h7 f5c8 b8b3 b8b4 b8b5 b8b6 b8b7 b8a8 b8c8 b8d8 b8e8 b8f8 b8g8 b8h8 c7b7 c7d7 c7c8 c7d8"
ALL4="d5d4 c2c3 e5f5 e5d6 e5e6"
TWO1="a2a3 a2a4"
TWO2="c3e2 c3e4"
TWO3="b8a8 b8b4"
TWO4="e5d6 e5e6"

k7_line () {  # name position-command go-command
  local name="$1" pos="$2" go="$3"
  local inp="$OUT/${name}_input.log" out="$OUT/${name}.txt"
  {
    grep -v '^\s*#\|^\s*$' "$JOB/pc20_all1024.opt" | while read -r n v; do echo "setoption name $n value $v"; done
    echo "isready"
    echo "ucinewgame"
    echo "isready"
    echo "$pos"
    echo "$go"
    echo "quit"
  } | tee "$inp" | "$EXE" > "$out" 2>&1
}

for i in 1 2 3 4; do
  case $i in
    1) POS="position startpos";;
    2) POS="position fen $F2";;
    3) POS="position fen $F3";;
    4) POS="position fen $F4";;
  esac
  eval "ALL=\$ALL$i"; eval "TWO=\$TWO$i"
  k7_line "k7_p${i}_plain" "$POS" "go depth 8"
  k7_line "k7_p${i}_all"   "$POS" "go depth 8 searchmoves $ALL"
  k7_line "k7_p${i}_two"   "$POS" "go depth 8 searchmoves $TWO"
done

echo "== eight numbers =="
for f in none_bench11 none_bench13 none_bench16 none_perft5 s14_bench11 s14_bench13 pc20_bench11 pc20_bench13; do
  printf '%-14s ' "$f"; grep -E "nodes" "$OUT/$f.txt" | tail -1
done
echo "== K7 cells (bestmove nodes cp) =="
for f in "$OUT"/k7_p*.txt; do
  printf '%-18s ' "$(basename "$f" .txt)"
  bm=$(grep "^bestmove" "$f" | tail -1 | awk '{print $2}')
  line=$(grep "^info depth" "$f" | tail -1)
  nodes=$(echo "$line" | grep -oE "nodes [0-9]+" | awk '{print $2}')
  cp=$(echo "$line" | grep -oE "score cp -?[0-9]+" | awk '{print $3}')
  echo "$bm $nodes $cp"
done
