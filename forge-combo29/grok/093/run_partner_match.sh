#!/usr/bin/env bash
# Partner binary, their IdeaK4 on versus off. Shrink stays at their default.
# 300 of my R openings, both colours = 600 games. S14, Threads 1, Hash 16, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
OPEN="$DIR/set_R.epd"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
cd "$DIR"
stdbuf -oL -eL "$FC" \
  -engine cmd="$EXE" name=PartnerOn option.IdeaK4=true \
  -engine cmd="$EXE" name=PartnerOff option.IdeaK4=false \
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
  -games 2 -rounds 300 -concurrency "$CONC" \
  -pgnout file="$DIR/match_partner_R.pgn" \
  > "$DIR/match_partner_fastchess.txt" 2>&1
echo "EXIT:$?" >> "$DIR/match_partner_fastchess.txt"
