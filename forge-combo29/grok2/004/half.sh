#!/usr/bin/env bash
# half.sh: C-HALF, the match.sh command with FULL at 20000 nodes and HALF at 10000, and no nodes= on -each.
P=/agent/repos/work/forge-combo29/build/forge              # arm 10: exe B
SW=IdeaB8         # e.g. IdeaB1 ; arm 10: HindsightDepth
FC=/home/ubuntu/fastchess/fastchess
rm -f "$3"
exec "$FC" -engine cmd="$P" name=FULL nodes=20000 option.$SW=false -engine cmd="$P" name=HALF nodes=10000 option.$SW=false \
  -each proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$1" format=epd order=sequential -rounds "$2" -repeat \
  -concurrency $(( $(nproc) > 1 ? $(nproc) - 1 : 1 )) -pgnout file="$3" "${@:4}"
