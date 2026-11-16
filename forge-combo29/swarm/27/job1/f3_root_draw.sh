#!/usr/bin/env bash
# f3_root_draw.sh <exe> <outdir>
# What the search does when the ROOT position is already a draw: src/search.cpp:2251-2270
# treats it as an adjudicated root and reports every depth up to the limit without searching,
# playing root_candidates.front() -- the first legal move in generation order.
set -u
EXE=$(readlink -f "${1:?exe}")
OUT="${2:?outdir}"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | grep -m1 '^id name')

case_run() {
  local label="$1" wait_s="$2"
  { cat "$OUT/$label.in"; sleep "$wait_s"; printf 'quit\n'; } | timeout 180 "$EXE" \
      > "$OUT/$label.raw.txt" 2> "$OUT/$label.stderr.txt"
  local rc=$?
  {
    echo "exe_started: $EXE"; echo "sha256: $SHA"; echo "id_name: $IDNAME"
    echo "input_file: $OUT/$label.in"; echo "input_lines:"; sed 's/^/  /' "$OUT/$label.in"
    echo "stdin_held_open_s: $wait_s"; echo "exit_code: $rc"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$OUT/$label.meta"
  echo "== $label rc=$rc"
  echo "   info lines: $(grep -cE '^info depth' "$OUT/$label.raw.txt")"
  grep -E '^info depth' "$OUT/$label.raw.txt" | head -3 | sed 's/^/   first: /'
  grep -E '^info depth' "$OUT/$label.raw.txt" | tail -1 | sed 's/^/   last:  /'
  grep -E '^bestmove' "$OUT/$label.raw.txt" | sed 's/^/   /'
}

hdr=$'uci\nisready\nsetoption name Hash value 16\nsetoption name Threads value 1\nsetoption name MultiPV value 1\nucinewgame\nisready\n'

# startpos appears three times after this move list (a real threefold repetition on the board)
MOVES="g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"

printf '%sposition startpos moves %s\ngo depth 10\n' "$hdr" "$MOVES" > "$OUT/R_repeat_root_depth10.in"
case_run R_repeat_root_depth10 6

# control: the same move list one ply shorter (startpos appears twice: no claim yet)
printf '%sposition startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6\ngo depth 10\n' "$hdr" > "$OUT/R_control_depth10.in"
case_run R_control_depth10 8

# fifty-move: root already at the hundredth half-move, white to move, not in check
FIFTY="4k3/8/8/8/8/8/8/4K2R w - - 100 60"
printf '%sposition fen %s\ngo depth 10\n' "$hdr" "$FIFTY" > "$OUT/R_fifty_root_depth10.in"
case_run R_fifty_root_depth10 6

echo
echo "| case | info lines | first info line | last info line | bestmove |"
echo "|---|---|---|---|---|"
for l in R_repeat_root_depth10 R_control_depth10 R_fifty_root_depth10; do
  f="$OUT/$l.raw.txt"
  c=$(grep -cE '^info depth' "$f")
  fi=$(grep -E '^info depth' "$f" | head -1)
  la=$(grep -E '^info depth' "$f" | tail -1)
  bm=$(grep -E '^bestmove' "$f" | tail -1)
  echo "| $l | $c | \`$fi\` | \`$la\` | $bm |"
done
