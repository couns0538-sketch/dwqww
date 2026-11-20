#!/usr/bin/env bash
# Match a partner build, switch on against switch off, 300 R openings, both colours.
set -u
OPT=${1:?option name}
EXE=${2:?exe path}
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
OUT=$REPO/forge-combo29/grok/$S
FC=/tmp/fastchess/fastchess
cd "$OUT"
{
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "option $OPT"
  echo "exe $EXE"
  sha256sum "$EXE"
  "$FC" -version
} > "$OUT/partner_match.log"
"$FC" \
  -engine cmd="$EXE" name=partner-on option."$OPT"=true \
  -engine cmd="$EXE" name=partner-off option."$OPT"=false \
  -each nodes=20000 option.Hash=16 option.Threads=1 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OUT/R.epd" format=epd order=sequential \
  -rounds 300 -repeat -concurrency 3 \
  -pgnout file="$OUT/partner_match.pgn" notation=uci min=true nodes=true \
  >> "$OUT/partner_match.log" 2>&1
echo "match_exit $?" >> "$OUT/partner_match.log"
