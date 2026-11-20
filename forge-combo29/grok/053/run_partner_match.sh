#!/usr/bin/env bash
# Partner switch, 300 R openings, both colours, 600 games. Option name is $1.
set -u
OPT="${1:?option name}"
S=$(cat ~/grok_seat.txt)
OUT="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE="${2:?exe}"
cd "$OUT"
sha256sum "$EXE" | awk '{print $1}' > partner_match.exe.sha
{
  echo "exe=$EXE"
  echo "sha256=$(cat partner_match.exe.sha)"
  echo "option=$OPT"
  echo "openings=R300"
  echo "rounds=300"
  echo "games=2"
  echo "concurrency=3"
  echo "nodes=20000"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > partner_match.meta
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on "option.${OPT}=true" \
  -engine cmd="$EXE" name=off "option.${OPT}=false" \
  -each proto=uci nodes=20000 \
        option.Threads=1 option.Hash=16 option.OwnBook=false option.Ponder=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OUT/R300.epd" format=epd order=sequential \
  -rounds 300 -games 2 \
  -concurrency 3 \
  -pgnout file="$OUT/partner_match.pgn" notation=uci min=true append=false \
  -ratinginterval 100 \
  > "$OUT/partner_match.fastchess.txt" 2>&1
echo "fastchess_exit=$?" >> partner_match.meta
