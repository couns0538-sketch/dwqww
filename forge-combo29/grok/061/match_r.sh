#!/usr/bin/env bash
# Second match of this seat's patch: 300 R openings, both colours, 600 games.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/tmp/forge-p/forge
FC=/tmp/fastchess/fastchess
OPTS="option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
"$FC" \
  -engine cmd="$EXE" name=s25on nodes=20000 $OPTS option.IdeaS25=true \
  -engine cmd="$EXE" name=s25off nodes=20000 $OPTS option.IdeaS25=false \
  -openings file="$D/R.fens" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -pgnout file="$D/match_r.pgn" notation=uci nodes=true \
  > "$D/match_r.txt" 2>&1
echo "EXIT:$?" >> "$D/match_r.txt"
