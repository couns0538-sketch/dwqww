#!/usr/bin/env bash
# s37 on vs s37 off, S14, Threads 1, Hash 16, 20000 nodes, O then G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-rel/forge
FC=/tmp/fastchess/fastchess
cd "$DIR"
cat /tmp/kimi5/forge-combo29/tests_kimi5_job3/first200.fens /tmp/kimi5/forge-combo29/tests_kimi5_job5/set_G.epd > OG.epd
LOG="$DIR/match_og.log"
{
  echo "openings $(wc -l < OG.epd)"
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $EXE"
  sha256sum "$EXE"
  echo "fastchess $FC"
  "$FC" -version || true
} > "$LOG"
"$FC" \
  -engine cmd="$EXE" name=s37on option.IdeaS37=true \
  -engine cmd="$EXE" name=s37off option.IdeaS37=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$DIR/match_og.pgn" notation=uci nodes=true \
  >> "$LOG" 2>&1
code=$?
{
  echo "fastchess_exit $code"
  echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG"
echo "fastchess_exit $code"
exit "$code"
