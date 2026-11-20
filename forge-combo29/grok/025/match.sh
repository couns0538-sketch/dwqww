#!/usr/bin/env bash
# IdeaS33 on versus IdeaS33 off. Both S14, Threads 1, Hash 16, 20000 nodes.
# OwnBook is forced off so a book move cannot replace the node-limited search.
# Openings are O then G (553), both colours (games 2) = 1106 games.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/agent/repos/work-build/forge
OUT="forge-combo29/grok/$S"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=s33on option.IdeaS33=true \
  -engine cmd="$EXE" name=s33off option.IdeaS33=false \
  -each \
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
    option.Threads=1 \
    option.Hash=16 \
    option.OwnBook=false \
    nodes=20000 \
  -openings "file=${OUT}/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency 3 \
  -pgnout "file=${OUT}/match_on_vs_off.pgn" nodes=true \
  > "${OUT}/match_on_vs_off.txt" 2>&1
echo "EXIT:$?" >> "${OUT}/match_on_vs_off.txt"
