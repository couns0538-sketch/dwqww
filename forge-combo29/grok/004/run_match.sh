#!/usr/bin/env bash
# Match exe P with LmrLateParentRelief on against the same exe with it off.
# Both sides use S14, Threads 1, Hash 16, 20000 nodes a move.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
ROUNDS=${1:-553}
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
OUT=$REPO/forge-combo29/grok/$S
OPEN=$OUT/openings_OG.epd
cd "$OUT"
{
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "rounds $ROUNDS"
  echo "exe $EXE"
  sha256sum "$EXE"
  "$FC" -version
} > "$OUT/match_on_vs_off.log"
"$FC" \
  -engine cmd="$EXE" name=relief-on option.LmrLateParentRelief=true \
  -engine cmd="$EXE" name=relief-off option.LmrLateParentRelief=false \
  -each nodes=20000 option.Hash=16 option.Threads=1 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -pgnout file="$OUT/match_on_vs_off.pgn" notation=uci min=true nodes=true \
  >> "$OUT/match_on_vs_off.log" 2>&1
echo "match_exit $?" >> "$OUT/match_on_vs_off.log"
