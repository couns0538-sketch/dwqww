#!/usr/bin/env bash
# profile_R.sh EXE FENS OUTDIR DEPTH NPROF : S14 + OwnBook false, depth DEPTH over FENS, under perf.
# Every setoption and position is followed by isready and the answer is scanned for refusal lines.
set -u
EXE="${1:?exe}"; FENS="${2:?fens}"; OUT="${3:?outdir}"; DEPTH="${4:-10}"; LIMIT="${5:-200}"
mkdir -p "$OUT"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
EXE_ABS="$(readlink -f "$EXE")"
head -n "$LIMIT" "$FENS" > "$OUT/positions.txt"

# build the command stream
{
  echo uci
  echo isready
  for o in "LmrQuietBase 93" "LmrQuietDivisor 205" "LmrNoisyBase 13" "LmrNoisyDivisor 333" \
           "LmrHistoryDivisor 5643" "NullMoveBase 5" "LmpBase 8" "HistoryPruneMultiplier 2220" \
           "HistoryBonusQuadratic 24" "HistoryBonusLinear 54" "HistoryBonusMax 2212" \
           "SingularDepth 6" "IirDepth 2" "NonPawnCorrection true" "OwnBook false"; do
    echo "setoption name ${o% *} value ${o##* }"
    echo isready
  done
  while IFS= read -r fen; do
    echo "position fen $fen"
    echo isready
    echo "go depth $DEPTH"
  done < "$OUT/positions.txt"
  echo quit
} > "$OUT/stream.txt"

{
  echo "exe $EXE_ABS"; sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "perf: $("$PERF" --version)"; echo "perf_event_paranoid: $(cat /proc/sys/kernel/perf_event_paranoid)"
  echo "positions: $(wc -l < "$OUT/positions.txt") from $FENS (first $LIMIT)"
  echo "depth: $DEPTH"
  echo "options: S14 + OwnBook false, isready after each; every position followed by isready"
  echo "command: perf record -o DATA -F 1999 -g -- EXE < stream.txt   (DATA deleted after reports)"
  echo "cores: $(nproc)"; echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/profile.meta" 2>&1

"$PERF" record -o "$OUT/perf.data" -F 1999 -g -- "$EXE_ABS" < "$OUT/stream.txt" \
  > "$OUT/search.stdout.txt" 2> "$OUT/perf.record.stderr.txt"
echo "record exit $?" >> "$OUT/profile.meta"

# refusal scan: the brief's STOP conditions
grep -nE "unknown option|invalid value|invalid FEN|illegal move" "$OUT/search.stdout.txt" > "$OUT/refusals.txt" || true
echo "refusal lines: $(wc -l < "$OUT/refusals.txt")" >> "$OUT/profile.meta"

"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --sort symbol \
  > "$OUT/perf_symbols_all.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --children --sort symbol > "$OUT/perf_children.txt" 2>&1
rm -f "$OUT/perf.data"
date -u
echo "bestmoves: $(grep -c '^bestmove' "$OUT/search.stdout.txt") for $(wc -l < "$OUT/positions.txt") positions"
grep -E '^# Samples:' "$OUT/perf_symbols_all.txt"
