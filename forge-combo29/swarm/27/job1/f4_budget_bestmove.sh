#!/usr/bin/env bash
# f4_budget_bestmove.sh <exe> <outdir>
# What move does the engine answer when a search budget ends before ONE root iteration finishes?
# src/search.cpp:2273-2277 answers at once for nodes==0; otherwise the root iteration aborts, no
# PV is published, and src/search.cpp:2639-2640 substitutes root_candidates.front(), which is the
# first legal move in generation order (perft 1 lists a2a3 first from startpos).
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
  local nfo bm
  nfo=$(grep -cE '^info depth' "$OUT/$label.raw.txt")
  bm=$(grep -E '^bestmove' "$OUT/$label.raw.txt" | tail -1)
  echo "== $label rc=$rc info_lines=$nfo $bm"
}

HDR='uci
isready
setoption name Hash value 16
setoption name Threads value 1
setoption name MultiPV value 1
setoption name Move Overhead value 10
setoption name OwnBook value false
ucinewgame
isready
position startpos'

for n in 0 1 10 20 26 30 100; do
  printf '%s\ngo nodes %s\n' "$HDR" "$n" > "$OUT/N_${n}.in"
  case_run "N_${n}" 3
done

# a clock search whose whole budget is below one iteration: movetime 1 (1 ms - 10 ms overhead)
for mt in 1 5 11 50; do
  printf '%s\ngo movetime %s\n' "$HDR" "$mt" > "$OUT/M_${mt}.in"
  case_run "M_${mt}" 3
done

# an empty clock: wtime 1000 with Move Overhead 1000 leaves nothing after overhead
printf '%s\nsetoption name Move Overhead value 1000\nisready\ngo wtime 1000 btime 1000\n' "$HDR" > "$OUT/W_empty_clock.in"
case_run "W_empty_clock" 3

echo
echo "| case | info lines | last info line | bestmove |"
echo "|---|---|---|---|"
for l in N_0 N_1 N_10 N_20 N_26 N_30 N_100 M_1 M_5 M_11 M_50 W_empty_clock; do
  f="$OUT/$l.raw.txt"
  c=$(grep -cE '^info depth' "$f")
  la=$(grep -E '^info depth' "$f" | tail -1)
  bm=$(grep -E '^bestmove' "$f" | tail -1)
  echo "| $l | $c | \`$la\` | $bm |"
done
