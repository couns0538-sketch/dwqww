#!/usr/bin/env bash
# IdeaS33 on versus off. S14, Threads 1, Hash 16, 20000 nodes, book off.
# Openings are O then G (553). games 2 is both colours: 1106 games.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=S33on option.IdeaS33=true \
  -engine cmd="$EXE" name=S33off option.IdeaS33=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/og_openings.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout file="$D/match_s33.pgn" notation=uci min=true
