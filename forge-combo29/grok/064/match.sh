#!/usr/bin/env bash
# IdeaS6 on versus IdeaS6 off. S14, Threads 1, Hash 16, 20000 nodes.
# OwnBook is false so a node limit is not answered from the book.
# 553 openings (O then G), both colours = 1106 games.
set -u
S=$(cat "$HOME/grok_seat.txt")
DIR="$(cat "$HOME/grok_repo.txt")/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
cd "$DIR"
SHARED="proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaS6on option.IdeaS6=true \
  -engine cmd="$EXE" name=IdeaS6off option.IdeaS6=false \
  -each $SHARED \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds 553 -repeat -concurrency 3 \
  -pgnout file="$DIR/match.pgn" notation=uci \
  -ratinginterval 100 \
  > "$DIR/match_stdout.txt" 2> "$DIR/match_stderr.txt"
echo "match exit $?" >> "$DIR/match_stdout.txt"
