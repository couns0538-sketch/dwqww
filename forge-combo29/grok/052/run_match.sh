#!/usr/bin/env bash
# fastchess match. rounds is the opening count; -repeat plays both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
ROUNDS="${1:-553}"
P=/agent/repos/work/forge-combo29/build-release/forge
FC=/tmp/fastchess/fastchess
OUT="$D/match_fastchess.txt"
PGN="$D/match.pgn"
rm -f "$PGN"
"$FC" \
  -engine cmd="$P" name=IdeaS28on option.IdeaS28=true \
  -engine cmd="$P" name=IdeaS28off option.IdeaS28=false \
  -each nodes=20000 tc=60+0 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/openings_OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 -recover \
  -ratinginterval 50 \
  -pgnout file="$PGN" notation=uci min=true \
  -event "grok-$S" \
  > "$OUT" 2>&1
echo MATCH_EXIT:$? >> "$OUT"
