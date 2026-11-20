#!/usr/bin/env bash
# Two copies of one exe, switch on versus switch off, fixed nodes, both colours.
# Usage: run_pair.sh EXE BOOK ROUNDS OPTION OUT_TXT PGN
set -euo pipefail
EXE="$1"
BOOK="$2"
ROUNDS="$3"
OPTION="$4"
OUT="$5"
PGN="$6"
rm -f "$PGN"
/home/ubuntu/fastchess/fastchess \
  -engine cmd="$EXE" name=on "option.${OPTION}=true" \
  -engine cmd="$EXE" name=off "option.${OPTION}=false" \
  -each option.Hash=16 option.Threads=1 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        option.OwnBook=false nodes=20000 \
  -openings file="$BOOK" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$PGN" notation=uci min=true \
  > "$OUT"
echo "WROTE $OUT"
tail -n 12 "$OUT"
