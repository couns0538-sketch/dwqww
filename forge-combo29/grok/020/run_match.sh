#!/usr/bin/env bash
# Match exe P with IdeaS22 on against the same exe with IdeaS22 off.
# S14, Threads 1, Hash 16, 20000 nodes. OwnBook false on both so the embedded
# book cannot move. rounds is the first argument (553 for O+G, both colours).
set -u
ROUNDS="${1:-553}"
OPENINGS="${2:-OG.epd}"
PGN="${3:-match_og.pgn}"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess-src/fastchess
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
exec "$FC" \
  -engine cmd="$EXE" name=s22on option.IdeaS22=true \
  -engine cmd="$EXE" name=s22off option.IdeaS22=false \
  -each proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false $S14 \
  -openings file="$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 -recover \
  -ratinginterval 200 -report penta=true \
  -pgnout file="$PGN" min=true \
  -event "IdeaS22 on vs off"
