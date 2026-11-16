#!/usr/bin/env bash
# pins.sh EXE LABEL OUTDIR — the four honesty pins and the S14 / PC20 bench figures.
# PINS ARE TAKEN WITH NO SETOPTION AT ALL (file 4 correction): a fresh process for each line.
# S14 and PC20 rows are separate: they need the setoptions first, then bench.
# Every line's raw output is kept; the .meta records exe path, sha256 and id name.
set -u
EXE=$1; LABEL=$2; OUT=$3
mkdir -p "$OUT"
{
  echo "exe: $EXE"
  sha256sum "$EXE"
  "$EXE" <<< "uci" 2>/dev/null | grep '^id name'
} > "$OUT/$LABEL.meta"
echo "nm __asan_: $(nm -C "$EXE" | grep -c __asan_)"

# PINS: no setoption
for b in 11 13 16; do
  printf 'uci\nisready\nbench %s\nquit\n' "$b" | "$EXE" > "$OUT/${LABEL}_pin_bench$b.txt" 2>&1
done
printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' | "$EXE" > "$OUT/${LABEL}_pin_perft5.txt" 2>&1

S14="setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
setoption name Hash value 16
setoption name OwnBook value false"

PC20="$S14
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true"

{ printf 'uci\nisready\n%s\nisready\n' "$S14"; printf 'bench 11\nisready\n'; printf 'bench 13\nisready\nquit\n'; } \
  | "$EXE" > "$OUT/${LABEL}_s14_bench.txt" 2>&1
{ printf 'uci\nisready\n%s\nisready\n' "$PC20"; printf 'bench 11\nisready\n'; printf 'bench 13\nisready\nquit\n'; } \
  | "$EXE" > "$OUT/${LABEL}_pc20_bench.txt" 2>&1

echo "--- $LABEL pins (no setoption) ---"
grep -h -E 'nodes [0-9]+' "$OUT/${LABEL}_pin_bench"*.txt | grep -oE 'bench depth [0-9]+ nodes [0-9]+'
grep -h 'nodes 4865609' "$OUT/${LABEL}_pin_perft5.txt" | head -1
echo "--- $LABEL S14 ---"
grep -E 'nodes [0-9]+' "$OUT/${LABEL}_s14_bench.txt" | grep -oE 'bench depth [0-9]+ nodes [0-9]+'
echo "--- $LABEL PC20 ---"
grep -E 'nodes [0-9]+' "$OUT/${LABEL}_pc20_bench.txt" | grep -oE 'bench depth [0-9]+ nodes [0-9]+'
echo "--- refusals (must be empty) ---"
grep -hiE 'unknown option|invalid value|ERROR' "$OUT/${LABEL}"_*.txt | head -5
