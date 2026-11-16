#!/usr/bin/env bash
# pc_pins.sh <exe> <outdir>
# Checks the three known-number rows of FABLE_TO_swarm_5.md on the PC build:
#   none (no setoption at all)        bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609
#   S14  (the 14 file-1 settings)     bench 11 = 242796,  bench 13 = 656517
#   PC20 (S14 + the six)              bench 11 = 278024,  bench 13 = 587276
# Every run is a FRESH PROCESS, Threads 1 (the swarm rule), stdin held open past bench so nothing is
# fabricated, and every option line is checked against the exe's own `uci` list first.
set -u
EXE=$(readlink -f "${1:?exe}")
OUT="${2:?outdir}"
mkdir -p "$OUT"
SHA=$(sha256sum "$EXE" | awk '{print $1}')

S14='LmrQuietBase 93
LmrQuietDivisor 205
LmrNoisyBase 13
LmrNoisyDivisor 333
LmrHistoryDivisor 5643
NullMoveBase 5
LmpBase 8
HistoryPruneMultiplier 2220
HistoryBonusQuadratic 24
HistoryBonusLinear 54
HistoryBonusMax 2212
SingularDepth 6
IirDepth 2
NonPawnCorrection true'

PC20_EXTRA='CuckooRep true
HistRework 2
TtPruneV2 true
CorrHistV2 true
MateAlphaGuard true
OwnBook false'

# --- what options does the exe actually advertise?
printf 'uci\nquit\n' | "$EXE" > "$OUT/uci.txt" 2>&1
printf 'uci\nquit\n' | "$EXE" > /dev/null 2>&1
ADVERTISED=$(printf 'uci\nquit\n' | "$EXE" 2>/dev/null | sed -n 's/^option name \(.*\) type .*/\1/p')
echo "advertised options: $(echo "$ADVERTISED" | wc -l)"

check_options() { # check_options <label> <newline-list of "Name value">
  local label="$1" list="$2" bad=0
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    local name="${line% *}"
    if ! echo "$ADVERTISED" | grep -qxF "$name"; then
      echo "  MISSING OPTION for $label: '$name' is not in the uci list"; bad=1
    fi
  done <<< "$list"
  return $bad
}

send_block() { # send_block <newline-list of "Name value">
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    printf 'setoption name %s value %s\n' "${line% *}" "${line##* }"
    printf 'isready\n'
  done <<< "$1"
}

run_bench() { # run_bench <label> <depth> <setoption-block or empty> <threads-line or empty>
  local label="$1" depth="$2" block="${3:-}" extra="${4:-0}"
  local inp="$OUT/${label}_bench${depth}.in"
  {
    printf 'uci\nisready\n'
    if [ "$extra" -gt 0 ]; then printf 'setoption name Threads value %s\nisready\n' "$extra"; fi
    [ -n "$block" ] && send_block "$block"
    printf 'ucinewgame\nisready\nposition startpos\nbench %s\n' "$depth"
  } > "$inp"
  { cat "$inp"; sleep 30; printf 'quit\n'; } | timeout 600 "$EXE" > "$OUT/${label}_bench${depth}.raw.txt" 2>&1
  local rc=$?
  local nodes
  nodes=$(grep -oE 'bench depth [0-9]+ nodes [0-9]+' "$OUT/${label}_bench${depth}.raw.txt" | tail -1 | awk '{print $5}')
  local bad
  bad=$(grep -cE 'unknown option|invalid value|ERROR' "$OUT/${label}_bench${depth}.raw.txt" || true)
  echo "$label bench $depth: nodes=${nodes:-NONE} rc=$rc badlines=$bad"
}

echo
echo "=== pins, no setoption at all (fresh process each), Threads default 1 ==="
for d in 11 13 16; do run_bench none "$d" ""; done
{ printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo perft 5\n'; sleep 20; printf 'quit\n'; } \
  | timeout 300 "$EXE" > "$OUT/none_perft5.raw.txt" 2>&1
echo "none perft 5: nodes=$(grep -E '^nodes ' "$OUT/none_perft5.raw.txt" | awk '{print $2}')"

echo
echo "=== S14 row (Threads 1, Hash 16) ==="
check_options S14 "$S14" || echo "  ^^ a named option is missing from the exe"
S14_FULL="Hash 16
$S14"
run_bench s14 11 "$S14_FULL"
run_bench s14 13 "$S14_FULL"

echo
echo "=== PC20 row (S14 + the six) ==="
check_options PC20 "$PC20_EXTRA" || echo "  ^^ a named option is missing from the exe"
PC20_FULL="Hash 16
$S14
$PC20_EXTRA"
run_bench pc20 11 "$PC20_FULL"
run_bench pc20 13 "$PC20_FULL"

echo
{
  echo "# PC build pins, exe $EXE"
  echo "# sha256 $SHA"
  echo "# date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# advertised options: $(echo "$ADVERTISED" | wc -l)"
  echo
  echo "| settings | bench 11 | bench 13 | bench 16 | perft 5 |"
  echo "|---|---|---|---|---|"
  echo "| none | $(grep -oE 'nodes [0-9]+' "$OUT/none_bench11.raw.txt" | tail -1 | awk '{print $2}') | $(grep -oE 'nodes [0-9]+' "$OUT/none_bench13.raw.txt" | tail -1 | awk '{print $2}') | $(grep -oE 'nodes [0-9]+' "$OUT/none_bench16.raw.txt" | tail -1 | awk '{print $2}') | $(grep -E '^nodes ' "$OUT/none_perft5.raw.txt" | awk '{print $2}') |"
  echo "| S14 (Threads 1, Hash 16) | $(grep -oE 'nodes [0-9]+' "$OUT/s14_bench11.raw.txt" | tail -1 | awk '{print $2}') | $(grep -oE 'nodes [0-9]+' "$OUT/s14_bench13.raw.txt" | tail -1 | awk '{print $2}') | - | - |"
  echo "| PC20 (Threads 1, Hash 16) | $(grep -oE 'nodes [0-9]+' "$OUT/pc20_bench11.raw.txt" | tail -1 | awk '{print $2}') | $(grep -oE 'nodes [0-9]+' "$OUT/pc20_bench13.raw.txt" | tail -1 | awk '{print $2}') | - | - |"
} | tee "$OUT/PINS.md"
