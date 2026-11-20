#!/usr/bin/env bash
# fastchess: IdeaS13 on versus IdeaS13 off, both S14, Threads 1, Hash 16, 20000 nodes.
# rounds = number of openings. games 2 = both colours. concurrency = nproc - 1.
set -u
EXE="$1"
OPENINGS="$2"
ROUNDS="$3"
OUT="$4"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
PGN="${OUT}.pgn"
LOG="${OUT}.txt"
/tmp/fastchess/fastchess \
  -concurrency "$CONC" \
  -rounds "$ROUNDS" \
  -games 2 \
  -openings "file=${OPENINGS}" format=epd order=sequential \
  -draw movenumber=40 movecount=8 score=10 \
  -resign movecount=4 score=800 \
  -maxmoves 200 \
  -pgnout "file=${PGN}" notation=uci \
  -engine cmd="$EXE" name=on nodes=20000 proto=uci \
    option.IdeaS13=true \
  -engine cmd="$EXE" name=off nodes=20000 proto=uci \
    option.IdeaS13=false \
  -each \
    option.Threads=1 \
    option.Hash=16 \
    option.OwnBook=false \
    option.LmrQuietBase=93 \
    option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 \
    option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 \
    option.SingularDepth=6 \
    option.IirDepth=2 \
    option.NonPawnCorrection=true \
    option.IdeaS13_Window=4 \
    option.IdeaS13_LmrDivisor=4096 \
    option.IdeaS13_LmrCap=1 \
  > "$LOG" 2>&1
echo "exit $?" >> "$LOG"
echo "wrote $LOG"
