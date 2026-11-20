#!/usr/bin/env bash
# Partner build: AspCappedReopen true against false, 300 R openings, both colours.
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build/forge
FC="$HOME/fastchess/fastchess"
TAG="${1:-partner_R}"
"$FC" \
  -engine cmd="$EXE" name=on nodes=20000 option.AspCappedReopen=true \
  -engine cmd="$EXE" name=off nodes=20000 option.AspCappedReopen=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$OUT/R300.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -ratinginterval 300 \
  -pgnout "file=$OUT/${TAG}.pgn" notation=uci min=true \
  -log "file=$OUT/${TAG}.log" level=warn append=false \
  -config "outname=$OUT/${TAG}_config.json"
