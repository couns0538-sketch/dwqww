#!/usr/bin/env bash
# IdeaS45 on versus off. Same exe. S14, Threads 1, Hash 16, 20000 nodes.
# 553 openings (O then G), both colours = 1106 games. concurrency = cores - 1.
set -u
SEAT="$(cat ~/grok_seat.txt)"
REPO="$(cat ~/grok_repo.txt)"
DIR="$REPO/forge-combo29/grok/$SEAT"
EXE="/agent/repos/work/forge-combo29/build/forge"
FC="/tmp/fastchess/fastchess"
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=s45on \
    option.IdeaS45=true option.IdeaS45_KingWorth=100000 option.IdeaS45_SeeMargin=0 \
  -engine cmd="$EXE" name=s45off \
    option.IdeaS45=false \
  -openings file="$DIR/match_og.epd" format=epd order=sequential \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -games 2 -rounds 553 -concurrency 3 \
  -pgnout file="$DIR/match_og.pgn" nodes=true \
  -ratinginterval 100 \
  > "$DIR/match_og.stdout.txt" 2> "$DIR/match_og.stderr.txt"
echo "match_exit=$?" | tee "$DIR/match_og.exit.txt"
