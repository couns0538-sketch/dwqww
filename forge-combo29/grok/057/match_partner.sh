#!/usr/bin/env bash
# Partner 007 switch: NullThreatVerify on versus off, depth spin at 14.
# 300 R openings, both colours, 20000 nodes, S14, Threads 1, Hash 16.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
EXE=/tmp/partner007/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
S14=(
  option.Threads=1
  option.Hash=16
  option.LmrQuietBase=93
  option.LmrQuietDivisor=205
  option.LmrNoisyBase=13
  option.LmrNoisyDivisor=333
  option.LmrHistoryDivisor=5643
  option.NullMoveBase=5
  option.LmpBase=8
  option.HistoryPruneMultiplier=2220
  option.HistoryBonusQuadratic=24
  option.HistoryBonusLinear=54
  option.HistoryBonusMax=2212
  option.SingularDepth=6
  option.IirDepth=2
  option.NonPawnCorrection=true
  option.NullThreatVerify_Depth=14
)
"$FC" \
  -engine cmd="$EXE" name=VerifyOn proto=uci "${S14[@]}" option.NullThreatVerify=true \
  -engine cmd="$EXE" name=VerifyOff proto=uci "${S14[@]}" option.NullThreatVerify=false \
  -each nodes=20000 \
  -openings file="$DIR/R300.fens" format=epd order=sequential \
  -rounds 300 -repeat \
  -concurrency 3 \
  -output format=fastchess \
  -ratinginterval 100 \
  -pgnout file="$DIR/match_partner.pgn" notation=uci \
  > "$DIR/match_partner.log" 2>&1
echo "fastchess_exit $?" >> "$DIR/match_partner.log"
