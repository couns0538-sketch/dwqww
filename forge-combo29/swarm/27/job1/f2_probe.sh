#!/usr/bin/env bash
# f2_probe.sh <exe> <outdir>
# Concrete, exactly reproducible behaviours of the search that the reading of src/search.cpp predicts.
# Each case is a whole UCI session; stdin is held open past the go line so the search is never
# cut short by EOF (a harness trap I hit and fixed).
set -u
EXE=$(readlink -f "${1:?exe}")
OUT="${2:?outdir}"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | grep -m1 '^id name')

case_run() { # case_run <label> <wait_s> ; session text already in $OUT/<label>.in
  local label="$1" wait_s="$2"
  { cat "$OUT/$label.in"; sleep "$wait_s"; printf 'quit\n'; } | timeout 180 "$EXE" \
      > "$OUT/$label.raw.txt" 2> "$OUT/$label.stderr.txt"
  local rc=$?
  {
    echo "exe_started: $EXE"; echo "sha256: $SHA"; echo "id_name: $IDNAME"
    echo "input_file: $OUT/$label.in"; echo "input_lines:"; sed 's/^/  /' "$OUT/$label.in"
    echo "stdin_held_open_s: $wait_s"; echo "exit_code: $rc"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "bad_lines:"; grep -nE 'unknown option|invalid value|invalid FEN|illegal move' "$OUT/$label.raw.txt" | sed 's/^/  /' || true
  } > "$OUT/$label.meta"
  echo "== $label rc=$rc"
  grep -E '^(info|bestmove|nodes)' "$OUT/$label.raw.txt" | tail -5 | sed 's/^/   /'
}

hdr=$'uci\nisready\nsetoption name Hash value 16\nsetoption name Threads value 1\nsetoption name MultiPV value 1\nucinewgame\nisready\nposition startpos\n'

# A. `go nodes 0`: src/search.cpp:2273-2277 answers at once with the first legal root move, depth 0.
printf '%sgo nodes 0\n' "$hdr" > "$OUT/A_go_nodes_0.in"
case_run A_go_nodes_0 2

# B. `go nodes 1`: one node of budget. src/search.cpp:1419/1561 test the budget before counting,
#    and the root iteration finishes only by aborting, so the answer is the first root move too.
printf '%sgo nodes 1\n' "$hdr" > "$OUT/B_go_nodes_1.in"
case_run B_go_nodes_1 2

# C. control: `go depth 1` really searches and reports one info line.
printf '%sgo depth 1\n' "$hdr" > "$OUT/C_go_depth_1.in"
case_run C_go_depth_1 2

# D. hashfull sampling: hashfull() reads only the first 1000 clusters (src/search.cpp:2561-2572).
#    Same search, 16 MB then 1024 MB: the reported hashfull is a 0.38 % / 0.006 % sample.
for mb in 16 1024; do
  printf 'uci\nisready\nsetoption name Hash value %s\nsetoption name Threads value 1\nsetoption name MultiPV value 1\nucinewgame\nisready\nposition startpos\ngo depth 13\n' "$mb" > "$OUT/D_hashfull_${mb}.in"
  case_run "D_hashfull_${mb}" 25
done

echo
echo "| case | bestmove line | max info depth | nodes on last info | hashfull on last info |"
echo "|---|---|---|---|---|"
for l in A_go_nodes_0 B_go_nodes_1 C_go_depth_1 D_hashfull_16 D_hashfull_1024; do
  f="$OUT/$l.raw.txt"
  bm=$(grep -E '^bestmove' "$f" | tail -1)
  d=$(grep -oE '^info depth [0-9]+' "$f" | awk '{print $3}' | sort -n | tail -1)
  n=$(grep -E '^info depth' "$f" | tail -1 | grep -oE 'nodes [0-9]+' | awk '{print $2}')
  h=$(grep -E '^info depth' "$f" | tail -1 | grep -oE 'hashfull [0-9]+' | awk '{print $2}')
  echo "| $l | ${bm:-none} | ${d:-none} | ${n:-none} | ${h:-none} |"
done
