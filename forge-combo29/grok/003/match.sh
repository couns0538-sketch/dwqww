#!/usr/bin/env bash
# IdeaS38 on versus off. Same exe. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G. games 2 swaps colours. concurrency = nproc - 1.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/home/ubuntu/fastchess/fastchess
cat "$DIR/O.fens" "$DIR/G.epd" > "$DIR/OG.epd"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "id_name=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -1)"
  echo "fastchess=$FC"
  echo "concurrency=$CONC"
  echo "cores=$CORES"
  echo "openings=$DIR/OG.epd"
  echo "opening_lines=$(wc -l < "$DIR/OG.epd")"
  echo "options:"
  echo "setoption name LmrQuietBase value 93"
  echo "setoption name LmrQuietDivisor value 205"
  echo "setoption name LmrNoisyBase value 13"
  echo "setoption name LmrNoisyDivisor value 333"
  echo "setoption name LmrHistoryDivisor value 5643"
  echo "setoption name NullMoveBase value 5"
  echo "setoption name LmpBase value 8"
  echo "setoption name HistoryPruneMultiplier value 2220"
  echo "setoption name HistoryBonusQuadratic value 24"
  echo "setoption name HistoryBonusLinear value 54"
  echo "setoption name HistoryBonusMax value 2212"
  echo "setoption name SingularDepth value 6"
  echo "setoption name IirDepth value 2"
  echo "setoption name NonPawnCorrection value true"
  echo "setoption name Threads value 1"
  echo "setoption name Hash value 16"
  echo "engine1 IdeaS38 true"
  echo "engine2 IdeaS38 false"
} > "$DIR/match.meta"
"$FC" \
  -engine cmd="$EXE" name=IdeaS38on option.IdeaS38=true \
  -engine cmd="$EXE" name=IdeaS38off option.IdeaS38=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 -concurrency "$CONC" \
  -pgnout file="$DIR/match.pgn" notation=uci \
  > "$DIR/match.txt" 2>&1
echo "MATCH_EXIT:$?"
tail -n 30 "$DIR/match.txt"
