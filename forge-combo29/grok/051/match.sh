#!/usr/bin/env bash
# IdeaE2 on versus IdeaE2 off. S14, Threads 1, Hash 16, 20000 nodes.
# One opening file, both colours: rounds = number of openings, games = 2.
# Concurrency = cores - 1.
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
  -ratinginterval 50 \
  -engine name=IdeaE2on cmd="$exe" option.IdeaE2=true \
  -engine name=IdeaE2off cmd="$exe" option.IdeaE2=false \
  -each proto=uci nodes=20000 \
    option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    option.IdeaE2_Span=100 \
  > "$out_dir/fastchess.txt" 2> "$out_dir/fastchess.err"
echo "fastchess_exit $?" >> "$out_dir/fastchess.txt"
echo "concurrency $conc" >> "$out_dir/fastchess.txt"
echo "rounds $rounds" >> "$out_dir/fastchess.txt"
echo "exe $exe" >> "$out_dir/fastchess.txt"
