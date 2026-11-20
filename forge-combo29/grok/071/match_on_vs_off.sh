#!/usr/bin/env bash
# IdeaS26 on versus IdeaS26 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G (553), both colours, one pass. Concurrency = nproc - 1.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/build-work/forge
cd "$DIR"
cat O.fens G.epd > OG.epd
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaS26on option.IdeaS26=true option.IdeaS26_Floor=6 option.IdeaS26_HighDepth=8 \
  -engine cmd="$EXE" name=IdeaS26off option.IdeaS26=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency "$CONC" \
  -pgnout file="$DIR/match_on_vs_off.pgn" notation=uci \
  -ratinginterval 100
