#!/usr/bin/env bash
# Partner switch, 300 R openings, both colours. This seat's script.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/tmp/forge-partner/forge
OUT="$(pwd)/$D"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on proto=uci nodes=20000 option.IdeaS32=true option.IdeaS32_OwedSlack=0 \
  -engine cmd="$EXE" name=off proto=uci nodes=20000 option.IdeaS32=false option.IdeaS32_OwedSlack=0 \
  -each option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$OUT/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout "file=$OUT/partner_match.pgn"
