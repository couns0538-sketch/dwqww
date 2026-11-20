#!/usr/bin/env bash
# exe P, switch true (on) vs switch false (off). S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G. Both colours. Concurrency = cores - 1.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
P=/agent/repos/work/forge-combo29/build/forge
cat O.fens G.epd > OG.epd
echo "openings $(wc -l < OG.epd)"
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
  -engine cmd="$P" name=on proto=uci "${OPTS[@]}" option.LmrLateParentRelief=true \
  -engine cmd="$P" name=off proto=uci "${OPTS[@]}" option.LmrLateParentRelief=false \
  -each nodes=20000 \
  -openings file="$PWD/OG.epd" format=epd order=sequential \
  -games 2 -rounds 553 \
  -concurrency 3 \
  -ratinginterval 100 \
  -pgnout file="$PWD/match_on_off.pgn" \
  > "$PWD/match_on_off.out" 2> "$PWD/match_on_off.err"
echo MATCH_EXIT:$?
