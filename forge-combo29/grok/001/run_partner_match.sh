#!/usr/bin/env bash
# Partner seat 051, IdeaE2 true vs false. 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OPEN="forge-combo29/grok/$S/R300.epd"
EXE="/tmp/p051/forge-combo29/build/forge"
FC="/tmp/fastchess/fastchess"
TAG="partner_match_R"
OUT="forge-combo29/grok/$S/${TAG}.txt"
PGN="forge-combo29/grok/$S/${TAG}.pgn"
ROUNDS=$(grep -cve '^$' "$OPEN")
rm -f config.json "$PGN"
OPTS=(
  option.Hash=16
  option.Threads=1
  option.OwnBook=false
  option.IdeaE2_Span=100
  option.LmrQuietBase=93
  option.LmrQuietDivisor=205
  option.LmrNoisyBase=13
  option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643
  option.NullMoveBase=5
  option.LmpBase=8
  option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24
  option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212
  option.SingularDepth=6
  option.IirDepth=2
  option.NonPawnCorrection=true
)
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "fastchess=$FC"
  echo "openings=$OPEN"
  echo "rounds=$ROUNDS"
  echo "concurrency=3"
  echo "switch=IdeaE2"
  date -u +%Y-%m-%dT%H:%M:%SZ
} > "forge-combo29/grok/$S/${TAG}.meta"
"$FC" \
  -engine cmd="$EXE" name=on proto=uci nodes=20000 option.IdeaE2=true "${OPTS[@]}" \
  -engine cmd="$EXE" name=off proto=uci nodes=20000 option.IdeaE2=false "${OPTS[@]}" \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -pgnout file="$PGN" notation=uci \
  > "$OUT" 2>&1
echo EXIT:$? >> "$OUT"
echo "wrote $OUT"
