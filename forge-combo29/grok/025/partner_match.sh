#!/usr/bin/env bash
# Partner seat 075, IdeaS33 on versus off, on the engine built from their patch.
# 300 R openings, both colours = 600 games. Nodes 20000, S14, Threads 1, Hash 16.
# Their spin defaults are sent explicitly: Thin 50, Large 300, Extra 2, Near 30.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
EXE=/agent/repos/partner-build/forge
OUT="forge-combo29/grok/$S"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=p075on option.IdeaS33=true \
  -engine cmd="$EXE" name=p075off option.IdeaS33=false \
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
    option.IdeaS33_Thin=50 \
    option.IdeaS33_Large=300 \
    option.IdeaS33_Extra=2 \
    option.IdeaS33_Near=30 \
    nodes=20000 \
  -openings "file=${OUT}/R.fens" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout "file=${OUT}/partner_match.pgn" nodes=true \
  > "${OUT}/partner_match.txt" 2>&1
echo "EXIT:$?" >> "${OUT}/partner_match.txt"
