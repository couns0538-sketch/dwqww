#!/usr/bin/env bash
# v3_profile.sh PERFBIN EXE NET OUTDIR : file 7 Step 1, the profile.
# Profiles `bench 13` under PC20 + the test net, Threads 1, Hash 16, then writes a text report of the symbol shares
# restricted to nnue::v3 and the search around it. Text only; no binary artefacts committed.
set -u
PERF="$1"; EXE="$2"; NET="$3"; OUT="$4"
mkdir -p "$OUT"
SCRIPT="$OUT/bench13.uci"

# the exact UCI script, written to a file FIRST (file 7's harness rule)
cat > "$SCRIPT" <<EOF
uci
isready
setoption name Threads value 1
isready
setoption name Hash value 16
isready
setoption name LmrQuietBase value 93
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
isready
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false
isready
setoption name NNUEArchFile value $NET
isready
setoption name NNUEArch value true
isready
ucinewgame
isready
bench 13
isready
quit
EOF

# the .meta file beside the output: exe path STARTED, its sha256, its id name, every option line sent
{
  echo "exe started: $EXE"
  sha256sum "$EXE"
  printf 'uci\nquit\n' | "$EXE" | grep '^id name'
  echo "--- option lines sent (in order):"
  grep '^setoption' "$SCRIPT"
  echo "--- bench output:"
  "$EXE" < "$SCRIPT" | grep -E 'bench depth|NNUE v3'
} > "$OUT/bench13.meta" 2>&1

# the profile itself
"$EXE" < "$SCRIPT" > "$OUT/bench13.raw" 2>&1
"$PERF" record -q -F 199 -g -o "$OUT/perf.data" -- "$EXE" < "$SCRIPT" > "$OUT/prof.raw" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --percent-limit 0.2 \
  > "$OUT/perf_report.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none \
  > "$OUT/perf_report_full.txt" 2>&1

echo "--- top symbols:"
grep -E '^ +[0-9]+\.[0-9]+%' "$OUT/perf_report.txt" | head -20
echo "--- nnue v3 symbols:"
grep -iE 'nnue' "$OUT/perf_report.txt" | head -20
