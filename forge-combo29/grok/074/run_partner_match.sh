#!/usr/bin/env bash
# Partner switch, 300 R openings, both colours. This seat's openings and harness.
set -u
EXE="/agent/repos/partner-024/forge-combo29/build/forge"
DIR="$(cd "$(dirname "$0")" && pwd)"
head -n 300 "$DIR/R.fens" > "$DIR/R300.fens"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds 300 \
  -games 2 \
  -openings file="$DIR/R300.fens" format=epd order=sequential \
  -pgnout file="$DIR/partner_match.pgn" append=false \
  -engine cmd="$EXE" name=on proto=uci option.IdeaS32=true \
  -engine cmd="$EXE" name=off proto=uci option.IdeaS32=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true
echo "PARTNER_MATCH_EXIT $?"
