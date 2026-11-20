#!/usr/bin/env bash
# Match a partner engine, switch on versus switch off, 300 R openings, both colours.
# S14, Threads 1, Hash 16, 20000 nodes, OwnBook off. Same adjudication as match.sh.
set -u
if [ "$#" -ne 3 ]; then
  echo "usage: partner_match.sh EXE OPTION_NAME OUT_PREFIX" >&2
  exit 2
fi
EXE=$1
OPT=$2
PREFIX=$3
S=$(cat ~/grok_seat.txt)
ROOT=$(cat ~/grok_repo.txt)
D="$ROOT/forge-combo29/grok/$S"
FC=/tmp/fastchess/fastchess
cd "$D"
"$FC" \
  -engine cmd="$EXE" name=on nodes=20000 \
    "option.${OPT}=true" \
  -engine cmd="$EXE" name=off nodes=20000 \
    "option.${OPT}=false" \
  -each option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$D/R.fens" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -draw movenumber=40 movecount=8 score=15 \
  -resign movecount=4 score=800 twosided=true \
  -ratinginterval 100 \
  -pgnout file="$D/${PREFIX}.pgn" nodes=true notation=uci
