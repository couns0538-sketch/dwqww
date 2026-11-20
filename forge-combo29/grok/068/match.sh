#!/usr/bin/env bash
# Test match: IdeaS16 on versus off. Both S14, Threads 1, Hash 16, 20000 nodes.
# OwnBook is turned off so every move is a search. Openings are O then G, each both colours.
# Draw and resign adjudication keeps a quiet game from playing out the fifty-move rule.
set -u
S=$(cat ~/grok_seat.txt)
ROOT=$(cat ~/grok_repo.txt)
D="$ROOT/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
ROUNDS=${1:-553}
cat "$D/O.fens" "$D/G.epd" > "$D/match_openings.epd"
cd "$D"
"$FC" \
  -engine cmd="$EXE" name=s16on nodes=20000 \
    option.IdeaS16=true option.IdeaS16_Order=4000 option.IdeaS16_Relief=1 \
  -engine cmd="$EXE" name=s16off nodes=20000 \
    option.IdeaS16=false \
  -each option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/match_openings.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -draw movenumber=40 movecount=8 score=15 \
  -resign movecount=4 score=800 twosided=true \
  -ratinginterval 100 \
  -pgnout file="$D/match.pgn" nodes=true notation=uci
