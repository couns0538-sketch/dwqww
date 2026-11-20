#!/usr/bin/env bash
# 553 openings, both colours, IdeaS27 on versus off, 20000 nodes, S14, Threads 1, Hash 16.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
BOOK="forge-combo29/grok/$S/openings_og.epd"
OUT="forge-combo29/grok/$S/match_og.txt"
PGN="forge-combo29/grok/$S/match_og.pgn"
stdbuf -oL -eL /tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-p/forge name=on proto=uci option.IdeaS27=true \
  -engine cmd=/tmp/forge-p/forge name=off proto=uci option.IdeaS27=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=${BOOK}" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout "file=${PGN}" \
  > "$OUT" 2>&1
echo "MATCH_EXIT $?" >> "$OUT"
