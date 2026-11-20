#!/usr/bin/env bash
# half.sh <openings.epd> <rounds> <out.pgn>: FULL (2,000 nodes) against HALF (1,000 nodes), both ideas off
P=$HOME/build/forge
FC=$HOME/fastchess_src/fastchess
rm -f "$3"
exec "$FC" -engine cmd="$P" name=FULL nodes=2000 option.IdeaB8=false option.HindsightDepth=false \
  -engine cmd="$P" name=HALF nodes=1000 option.IdeaB8=false option.HindsightDepth=false \
  -each proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$1" format=epd order=sequential -rounds "$2" -repeat \
  -concurrency $(( $(nproc) > 1 ? $(nproc) - 1 : 1 )) -pgnout file="$3"
