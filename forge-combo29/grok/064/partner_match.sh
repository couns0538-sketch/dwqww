#!/usr/bin/env bash
# Partner 014's IdeaS5, on versus off, on my R openings.
# 300 openings, both colours = 600 games. S14, Threads 1, Hash 16, 20000 nodes.
set -u
S=$(cat "$HOME/grok_seat.txt")
DIR="$(cat "$HOME/grok_repo.txt")/forge-combo29/grok/$S"
EXE=/tmp/partner014/forge-combo29/build/forge
cd "$DIR"
head -n 300 R.fens > partner_R300.fens
SHARED="proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaS5on option.IdeaS5=true \
  -engine cmd="$EXE" name=IdeaS5off option.IdeaS5=false \
  -each $SHARED \
  -openings file="$DIR/partner_R300.fens" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -pgnout file="$DIR/partner_match.pgn" notation=uci \
  -ratinginterval 100 \
  > "$DIR/partner_match_stdout.txt" 2> "$DIR/partner_match_stderr.txt"
echo "match exit $?" >> "$DIR/partner_match_stdout.txt"
