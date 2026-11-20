#!/usr/bin/env bash
# Partner 025, IdeaS33 on versus off, on the partner binary.
# 300 R openings, both colours, 600 games. S14, Threads 1, Hash 16, 20000 nodes.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/tmp/partner025/forge-combo29/build/forge
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=P25on option.IdeaS33=true option.IdeaS33_Max=3 option.IdeaS33_Divisor=80 option.IdeaS33_Near=40 \
  -engine cmd="$EXE" name=P25off option.IdeaS33=false option.IdeaS33_Max=3 option.IdeaS33_Divisor=80 option.IdeaS33_Near=40 \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/r_300.fen" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout file="$D/partner_025_match.pgn" notation=uci min=true
