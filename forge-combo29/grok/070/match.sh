#!/usr/bin/env bash
# 553 openings, both colours, 20000 nodes. Switch on versus switch off.
set -u
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/forge-work/forge
{
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe=$EXE"
  sha256sum "$EXE"
  /tmp/fastchess/fastchess \
    -engine cmd="$EXE" name=s22on option.IdeaS22=true option.IdeaS22_Ply=1 \
    -engine cmd="$EXE" name=s22off option.IdeaS22=false \
    -each option.Threads=1 option.Hash=16 \
      option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
      option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
      option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
      option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
      option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
      option.HistoryBonusMax=2212 option.SingularDepth=6 \
      option.IirDepth=2 option.NonPawnCorrection=true \
      option.OwnBook=false \
      nodes=20000 \
    -openings file="$DIR/match_OG.epd" format=epd order=sequential \
    -rounds 553 -games 2 -concurrency 3 \
    -pgnout file="$DIR/match.pgn"
  echo "fastchess_exit=$?"
  echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$DIR/match_fastchess.txt" 2>&1
