#!/usr/bin/env bash
# Partner binary, switch on versus switch off, 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/forge-partner/forge
FC=/tmp/fastchess/fastchess
"$FC" \
  -engine cmd="$EXE" name=P017on option.IdeaS15=true \
  -engine cmd="$EXE" name=P017off option.IdeaS15=false \
  -each option.Threads=1 option.Hash=16 nodes=20000 \
    option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$PWD/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="$PWD/match_partner_R.pgn" notation=uci \
  > "$PWD/match_partner_R.log" 2>&1
echo "EXIT:$?" >> "$PWD/match_partner_R.log"
