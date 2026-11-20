#!/usr/bin/env bash
# Partner 104 switch IdeaS35, true versus false. 300 R openings, both colours, 600 games.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
P=/agent/repos/partner104/forge-combo29/build/forge
echo "openings $(wc -l < R.fens)"
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
/tmp/fastchess/fastchess \
  -engine cmd="$P" name=on proto=uci "${OPTS[@]}" option.IdeaS35=true \
  -engine cmd="$P" name=off proto=uci "${OPTS[@]}" option.IdeaS35=false \
  -each nodes=20000 \
  -openings file="$PWD/R.fens" format=epd order=sequential \
  -games 2 -rounds 300 \
  -concurrency 3 \
  -ratinginterval 100 \
  -pgnout file="$PWD/partner104_match.pgn" \
  > "$PWD/partner104_match.out" 2> "$PWD/partner104_match.err"
echo PARTNER_MATCH_EXIT:$?
