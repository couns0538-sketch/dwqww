#!/usr/bin/env bash
# Partner engine, its IdeaA7 on versus off. 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE="$1"
OPEN="forge-combo29/grok/$S/positions_R.fens"
FC=/tmp/fastchess/fastchess
N=$(grep -c . "$OPEN")
OUT="forge-combo29/grok/$S/match_partner_R.txt"
PGN="forge-combo29/grok/$S/match_partner_R.pgn"
OPTS=(
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
  option.Threads=1
  option.Hash=16
)
"$FC" \
  -engine cmd="$EXE" name=P088on option.IdeaA7=true \
  -engine cmd="$EXE" name=P088off option.IdeaA7=false \
  -each nodes=20000 "${OPTS[@]}" \
  -openings "file=$OPEN" format=epd order=sequential \
  -rounds "$N" -repeat -concurrency 3 \
  -pgnout "file=$PGN" notation=uci nodes=true \
  > "$OUT" 2>&1
echo "match_exit $?" >> "$OUT"
echo "wrote $OUT rounds $N"
