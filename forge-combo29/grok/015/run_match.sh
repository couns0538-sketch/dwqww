#!/usr/bin/env bash
# Test match: IdeaS6 true vs IdeaS6 false. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G (553), both colours (1106 games). Concurrency = nproc - 1.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
OUT="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
CORES=$(nproc)
CONC=$((CORES - 1))
mkdir -p /tmp/fc-match
cd /tmp/fc-match
stdbuf -oL /tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=IdeaS6on option.IdeaS6=true \
  -engine cmd="$EXE" name=IdeaS6off option.IdeaS6=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$OUT/openings_og.epd" format=epd order=sequential \
  -rounds 553 -repeat -concurrency "$CONC" \
  -pgnout "file=$OUT/match.pgn" notation=uci nodes=true \
  > "$OUT/match_stdout.txt" 2>&1
echo "exit=$?" >> "$OUT/match_stdout.txt"
