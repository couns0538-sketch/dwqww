#!/usr/bin/env bash
# Test match: same exe, LmrSignedCorrection true vs false. S14, Threads 1, Hash 16, 20000 nodes.
set -u
SEAT=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$SEAT"
EXE="${1:?exe}"
OPENINGS="${2:?openings}"
ROUNDS="${3:?rounds}"
OUT="${4:?out-prefix}"
CONC="${5:-3}"
FC=/tmp/fastchess/fastchess
OPTS=(
  option.Threads=1 option.Hash=16
  option.LmrQuietBase=93 option.LmrQuietDivisor=205
  option.LmrNoisyBase=13 option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643 option.NullMoveBase=5
  option.LmpBase=8 option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212 option.SingularDepth=6
  option.IirDepth=2 option.NonPawnCorrection=true
)
"$FC" \
  -engine cmd="$EXE" name=signed proto=uci "${OPTS[@]}" option.LmrSignedCorrection=true \
  -engine cmd="$EXE" name=plain proto=uci "${OPTS[@]}" option.LmrSignedCorrection=false \
  -openings file="$OPENINGS" format=epd order=sequential \
  -each nodes=20000 \
  -games 2 -rounds "$ROUNDS" -concurrency "$CONC" \
  -config outname=/tmp/fastchess-seat-config.json \
  -pgnout file="$OUT.pgn" notation=uci nodes=true \
  > "$OUT.log" 2>&1
echo "exit=$?" >> "$OUT.log"
echo "wrote $OUT.log"
tail -n 30 "$OUT.log"
