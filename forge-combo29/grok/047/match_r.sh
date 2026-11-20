#!/usr/bin/env bash
# 300 R openings, both colours, 600 games. Switch true versus switch false.
# Usage: match_r.sh <exe> <option> <out_prefix>
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=$1
OPT=$2
PREFIX=$3
FC=/tmp/fastchess/fastchess
CONC=$(( $(nproc) - 1 ))
ROUNDS=$(wc -l < "$D/R.epd")
{
  echo "exe=$EXE"
  echo "option=$OPT"
  echo "fastchess=$FC"
  echo "concurrency=$CONC"
  echo "openings=$ROUNDS"
  echo "games=2"
  date -u +%Y-%m-%dT%H:%M:%SZ
} > "$D/${PREFIX}.meta"
"$FC" \
  -engine cmd="$EXE" name=on proto=uci option."$OPT"=true \
  -engine cmd="$EXE" name=off proto=uci option."$OPT"=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        nodes=20000 \
  -openings file="$D/R.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency "$CONC" \
  -pgnout file="$D/${PREFIX}.pgn" notation=uci nodes=true \
  > "$D/${PREFIX}.txt" 2> "$D/${PREFIX}.err"
echo "fastchess_exit=$?" >> "$D/${PREFIX}.meta"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$D/${PREFIX}.meta"
tail -n 20 "$D/${PREFIX}.txt"
