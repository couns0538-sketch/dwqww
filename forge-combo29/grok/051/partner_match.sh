#!/usr/bin/env bash
# Partner switch: EvalRule50Damp true versus false, span 100.
# 300 R openings, both colours. My script, not the partner's.
set -u
exe=$1
book=$2
out_dir=$3
cores=$(nproc)
conc=$((cores - 1))
if [ "$conc" -lt 1 ]; then conc=1; fi
rounds=$(grep -cve '^$' "$book")
mkdir -p "$out_dir"
rm -f "$out_dir/games.pgn"
/tmp/fastchess/fastchess \
  -concurrency "$conc" \
  -tournament roundrobin \
  -rounds "$rounds" \
  -games 2 \
  -openings file="$book" format=epd order=sequential \
  -pgnout file="$out_dir/games.pgn" notation=uci min=true append=false \
  -ratinginterval 100 \
  -engine name=DampOn cmd="$exe" option.EvalRule50Damp=true \
  -engine name=DampOff cmd="$exe" option.EvalRule50Damp=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    option.EvalRule50Damp_Span=100 \
  > "$out_dir/fastchess.txt" 2> "$out_dir/fastchess.err"
echo "fastchess_exit $?" >> "$out_dir/fastchess.txt"
echo "concurrency $conc" >> "$out_dir/fastchess.txt"
echo "rounds $rounds" >> "$out_dir/fastchess.txt"
echo "exe $exe" >> "$out_dir/fastchess.txt"
