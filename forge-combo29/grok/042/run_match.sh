#!/usr/bin/env bash
# IdeaK3 on versus off. Openings O then G, both colours, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/agent/repos/work/build/forge
FC=/tmp/fastchess/fastchess
OUT="$D/match_og.log"
PGN="$D/match_og.pgn"
rm -f "$PGN"
"$FC" \
  -engine cmd="$EXE" name=IdeaK3on option.IdeaK3=true \
  -engine cmd="$EXE" name=IdeaK3off option.IdeaK3=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/sets/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout file="$PGN" notation=uci \
  > "$OUT" 2>&1
echo "exit $?" >> "$OUT"
