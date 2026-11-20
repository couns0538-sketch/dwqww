#!/usr/bin/env bash
# Test match: IdeaB1 true vs IdeaB1 false. S14, Threads 1, Hash 16, 20000 nodes.
# Openings are O then G (553). Both colours: 1106 games. Concurrency = nproc - 1.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/forge-builds/work/forge
FAST=/tmp/fastchess/fastchess
OPEN="$DIR/openings_OG.epd"
cat /tmp/positions/first200.fens /tmp/positions/set_G.epd > "$OPEN"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
cd "$DIR"
"$FAST" \
  -engine cmd="$EXE" name=b1on option.IdeaB1=true \
  -engine cmd="$EXE" name=b1off option.IdeaB1=false \
  -each option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true option.Threads=1 option.Hash=16 \
        option.OwnBook=false nodes=20000 \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency "$CONC" \
  -pgnout file="$DIR/match.pgn" notation=uci \
  > "$DIR/match_fastchess.txt" 2>&1
echo "match exit $?" >> "$DIR/match_fastchess.txt"
