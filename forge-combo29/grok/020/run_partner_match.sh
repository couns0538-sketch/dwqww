#!/usr/bin/env bash
# Partner exe, IdeaS22 on vs off, my R openings, both colours.
set -u
EXE=/tmp/partner-build/forge
FC=/tmp/fastchess-src/fastchess
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
exec "$FC" \
  -engine cmd="$EXE" name=s22on option.IdeaS22=true \
  -engine cmd="$EXE" name=s22off option.IdeaS22=false \
  -each proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false $S14 \
  -openings file=R.fen format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 -recover \
  -ratinginterval 300 -report penta=true \
  -pgnout file=partner_match.pgn min=true \
  -event "partner 070 IdeaS22 on vs off R"
