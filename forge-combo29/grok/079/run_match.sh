#!/usr/bin/env bash
# Test match: IdeaB10 on vs off, S14, 20000 nodes, openings OG both colours.
set -u
S=$(cat ~/grok_seat.txt)
D="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
cd "$D"
/tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-p/forge name=IdeaB10on option.IdeaB10=true \
  -engine cmd=/tmp/forge-p/forge name=IdeaB10off option.IdeaB10=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    option.IdeaB10_Ratio=150 option.IdeaB10_MinNodes=32 option.IdeaB10_Step=100 option.IdeaB10_Cap=3 \
    option.OwnBook=false \
  -openings file="$D/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -resign movecount=6 score=800 twosided=true \
  -draw movenumber=50 movecount=8 score=10 \
  -maxmoves 200 \
  -pgnout file="$D/match.pgn" notation=uci nodes=true \
  -ratinginterval 100
