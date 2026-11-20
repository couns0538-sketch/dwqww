#!/usr/bin/env bash
# IdeaA8 true vs IdeaA8 false. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G, 553 positions, both colours, 1106 games. No repeated list.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
cat "$DIR/first200.fens" "$DIR/set_G.epd" > "$DIR/openings_OG.epd"
echo "openings $(wc -l < "$DIR/openings_OG.epd")"
exec /tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaA8on option.IdeaA8=true \
  -engine cmd="$EXE" name=IdeaA8off option.IdeaA8=false \
  -each option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true option.Threads=1 option.Hash=16 \
        nodes=20000 \
  -openings "file=$DIR/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout "file=$DIR/match_on_off.pgn" notation=uci \
  -event "grok-089 IdeaA8"
