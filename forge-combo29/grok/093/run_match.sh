#!/usr/bin/env bash
# IdeaK4 on versus IdeaK4 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G (553), both colours (games 2) = 1106 games.
# Concurrency is cores minus 1.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
OPEN="$DIR/openings_OG.epd"
cat /tmp/grok093_sets/first200.fens /tmp/grok093_sets/set_G.epd > "$OPEN"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
cd "$DIR"
stdbuf -oL -eL "$FC" \
  -engine cmd="$EXE" name=K4on option.IdeaK4=true option.IdeaK4_Shrink=24 \
  -engine cmd="$EXE" name=K4off option.IdeaK4=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 \
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
  -openings file="$OPEN" format=epd order=sequential \
  -games 2 -rounds 553 -concurrency "$CONC" \
  -pgnout file="$DIR/match_OG.pgn" \
  > "$DIR/match_fastchess.txt" 2>&1
echo "EXIT:$?" >> "$DIR/match_fastchess.txt"
