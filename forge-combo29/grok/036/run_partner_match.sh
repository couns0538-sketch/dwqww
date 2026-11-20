#!/usr/bin/env bash
set -u
EXE=/agent/repos/partner-086/forge-combo29/build/forge
OPEN="/agent/repos/dwqww/forge-combo29/grok/036/set_R.epd"
PGN="/agent/repos/dwqww/forge-combo29/grok/036/match_partner_R.pgn"
cd /tmp/match086
rm -f config.json
exec /tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaA5on option.IdeaA5=true option.IdeaA5_Divisor=2 \
  -engine cmd="$EXE" name=IdeaA5off option.IdeaA5=false option.IdeaA5_Divisor=2 \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -draw movenumber=40 movecount=8 score=10 \
  -resign movecount=5 score=900 twosided=true \
  -maxmoves 200 \
  -pgnout file="$PGN" notation=uci min=true \
  -ratinginterval 50 \
  -event IdeaA5-partner -site grok-036
