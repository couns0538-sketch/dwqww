#!/usr/bin/env bash
# f1_multipv_nodes.sh <exe> <outdir>
# Shows: with MultiPV >= 2, a `go nodes N` search ends far below N nodes while MultiPV 1
# reaches the node limit. Reading: src/search.cpp:2170-2173 sets the alternate MultiPV
# worker's node_limit_specified_ from its parent, but narrows its own node_limit_ to 0
# (search.cpp:2488-2489), so should_stop_with() trips at its first node (search.cpp:1273-1274).
# NOTE: the engine must not see EOF on stdin while it searches, or it answers at once;
# every case keeps stdin open until after bestmove by piping a short sleep before quit.
set -u
EXE=$(readlink -f "${1:?exe}")
OUT="${2:?outdir}"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | grep -m1 '^id name')

run() { # run <label> <body-file>   body-file holds the lines after the preamble, ending before bestmove wait
  local label="$1" body="$2"
  local inp="$OUT/$label.in"
  cat "$OUT/_preamble.in" "$body" > "$inp"
  local raw="$OUT/$label.raw.txt"
  { cat "$inp"; sleep "${WAIT_S:-6}"; printf 'quit\n'; } | timeout 120 "$EXE" > "$raw" 2> "$OUT/$label.stderr.txt"
  local rc=$?
  {
    echo "exe_started: $EXE"
    echo "sha256: $SHA"
    echo "id_name: $IDNAME"
    echo "input_file: $inp"
    echo "input_lines:"; sed 's/^/  /' "$inp"
    echo "stdin_held_open_until_quit: yes (sleep ${WAIT_S:-6} after the go line)"
    echo "exit_code: $rc"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "unknown_or_invalid_option_lines:"
    grep -E 'unknown option|invalid value|invalid FEN|illegal move' "$OUT/$label.raw.txt" | sed 's/^/  /' || true
  } > "$OUT/$label.meta"
  echo "== $label rc=$rc"
  grep -E '^info depth|^bestmove' "$raw" | tail -4 | sed 's/^/   /'
}

summary_row() { # summary_row <label>
  local f="$OUT/$1.raw.txt"
  local d m n bm
  d=$(grep -oE '^info depth [0-9]+' "$f" | awk '{print $3}' | sort -n | tail -1)
  m=$(grep -oE ' multipv [0-9]+' "$f" | awk '{print $2}' | sort -n | uniq | tr '\n' ',' | sed 's/,$//')
  n=$(grep -E '^info depth' "$f" | tail -1 | grep -oE 'nodes [0-9]+' | awk '{print $2}')
  bm=$(grep -E '^bestmove' "$f" | tail -1)
  echo "| $1 | ${d:-none} | ${m:-1} | ${n:-none} | $bm |"
}

# preamble without the options that the case body sets
cat > "$OUT/_preamble.in" <<'EOF'
uci
isready
setoption name Hash value 16
setoption name Threads value 1
EOF

labels=()
for mpv in 1 2 3; do
  cat > "$OUT/_body_mpv${mpv}_nodes.in" <<EOF
setoption name MultiPV value $mpv
isready
ucinewgame
isready
position startpos
go nodes 200000
EOF
  run "mpv${mpv}_nodes200k" "$OUT/_body_mpv${mpv}_nodes.in"; labels+=("mpv${mpv}_nodes200k")
done
for mpv in 1 2; do
  cat > "$OUT/_body_mpv${mpv}_depth8.in" <<EOF
setoption name MultiPV value $mpv
isready
ucinewgame
isready
position startpos
go depth 8
EOF
  run "mpv${mpv}_depth8" "$OUT/_body_mpv${mpv}_depth8.in"; labels+=("mpv${mpv}_depth8")
done

echo
echo "| case | max info depth | multipv indexes seen | nodes on last info line | bestmove |"
echo "|---|---|---|---|---|"
for l in "${labels[@]}"; do summary_row "$l"; done
