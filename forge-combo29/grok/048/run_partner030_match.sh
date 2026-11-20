#!/usr/bin/env bash
# Seat 030 IdeaB1 true vs false. 300 R openings, both colours, 600 games.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/home/ubuntu/fastchess/fastchess
LOG="$PWD/$OUT/partner030_match.log"
PGN="$PWD/$OUT/partner030_match.pgn"
{
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $EXE"
  sha256sum "$EXE"
  echo "fastchess $FC"
  sha256sum "$FC"
} > "$PWD/$OUT/partner030_match.meta.txt"
"$FC" \
  -concurrency 3 \
  -rounds 300 \
  -games 2 \
  -openings "file=$PWD/$OUT/R300.fens" format=epd order=sequential \
  -pgnout "file=$PGN" \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -engine "cmd=$EXE" name=IdeaB1_on option.IdeaB1=true \
  -engine "cmd=$EXE" name=IdeaB1_off option.IdeaB1=false \
  > "$LOG" 2>&1
echo "exit $? end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$PWD/$OUT/partner030_match.meta.txt"
