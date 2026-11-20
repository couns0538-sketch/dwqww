#!/usr/bin/env bash
# Match: IdeaK5 on versus IdeaK5 off. Both sides get S14, Threads 1, Hash 16, 20000 nodes.
# rounds = number of openings. games 2 = both colours. concurrency is cores minus 1.
set -u
EXE="${1:?exe}"
OPENINGS="${2:?openings}"
ROUNDS="${3:?rounds}"
OUTDIR="${4:?outdir}"
mkdir -p "$OUTDIR"
OPTS=(
  option.LmrQuietBase=93
  option.LmrQuietDivisor=205
  option.LmrNoisyBase=13
  option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643
  option.NullMoveBase=5
  option.LmpBase=8
  option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24
  option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212
  option.SingularDepth=6
  option.IirDepth=2
  option.NonPawnCorrection=true
  option.Threads=1
  option.Hash=16
)
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=K5on proto=uci nodes=20000 "${OPTS[@]}" option.IdeaK5=true \
  -engine cmd="$EXE" name=K5off proto=uci nodes=20000 "${OPTS[@]}" option.IdeaK5=false \
  -openings file="$OPENINGS" format=epd order=sequential \
  -games 2 -rounds "$ROUNDS" -concurrency 3 \
  -pgnout file="$OUTDIR/games.pgn" \
  > "$OUTDIR/fastchess.log" 2>&1
echo "exit $?" >> "$OUTDIR/fastchess.log"
