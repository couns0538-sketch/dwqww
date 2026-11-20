#!/usr/bin/env bash
# fastchess: exe P, NullSeeVeto on versus off, S14, Threads 1, Hash 16, 20000 nodes.
# rounds = number of openings; -repeat plays both colours.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess-src/fastchess
ROUNDS=${1:-553}
TAG=${2:-og}
"$FC" \
  -engine cmd="$EXE" name=veto_on option.NullSeeVeto=true \
  -engine cmd="$EXE" name=veto_off option.NullSeeVeto=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        nodes=20000 tc=60+0.6 \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -pgnout file="$DIR/match_${TAG}.pgn" notation=uci nodes=true
