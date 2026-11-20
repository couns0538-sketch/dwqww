#!/usr/bin/env bash
# IdeaS44 on versus IdeaS44 off. Same exe, S14, Threads 1, Hash 16, 20000 nodes.
# Openings are O then G (553). -games 2 plays both colours: 1106 games.
set -u
OUT="$(cd "$(dirname "$0")" && pwd)"
EXE=/agent/repos/work/forge-combo29/build/forge
cat "$OUT/O.fens" "$OUT/G.epd" > "$OUT/OG.epd"
exec "$HOME/fastchess/fastchess" \
  -engine cmd="$EXE" name=s44on option.IdeaS44=true \
  -engine cmd="$EXE" name=s44off option.IdeaS44=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OUT/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 -ratinginterval 100 \
  -pgnout file="$OUT/match_s44.pgn"
