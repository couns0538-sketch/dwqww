#!/usr/bin/env bash
# IdeaK9 true versus false, cap 3, openings O then G, both colours: 1106 games.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/home/ubuntu/fastchess/fastchess
LOG="$PWD/$OUT/k9_og_match.log"
PGN="$PWD/$OUT/k9_og_match.pgn"
{
  echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $EXE"
  sha256sum "$EXE"
  echo "fastchess $FC"
  sha256sum "$FC"
} > "$PWD/$OUT/k9_og_match.meta.txt"
"$FC" \
  -concurrency 3 \
  -rounds 553 \
  -games 2 \
  -openings "file=$PWD/$OUT/OG.fens" format=epd order=sequential \
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
    option.IdeaK9_Cap=3 \
  -engine "cmd=$EXE" name=IdeaK9_on option.IdeaK9=true \
  -engine "cmd=$EXE" name=IdeaK9_off option.IdeaK9=false \
  > "$LOG" 2>&1
echo "exit $? end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$PWD/$OUT/k9_og_match.meta.txt"
