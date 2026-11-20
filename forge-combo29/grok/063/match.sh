#!/usr/bin/env bash
# Match IdeaS15 on (s15on) against IdeaS15 off (s15off).
# S14, Threads 1, Hash 16, OwnBook false, 20000 nodes a move.
# rounds = number of openings; games 2 = both colours. Do not raise rounds past the book.
set -u
EXE=/agent/repos/work/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
OUT="$(cd "$(dirname "$0")" && pwd)"
ROUNDS="${1:-553}"
BOOK="${2:-$OUT/openings_OG.epd}"
TAG="${3:-match_og}"
CONC="${4:-3}"
"$FC" \
  -engine cmd="$EXE" name=s15on option.IdeaS15=true \
  -engine cmd="$EXE" name=s15off option.IdeaS15=false \
  -each proto=uci nodes=20000 \
    option.LmrQuietBase=93 \
    option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 \
    option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 \
    option.SingularDepth=6 \
    option.IirDepth=2 \
    option.NonPawnCorrection=true \
    option.Threads=1 \
    option.Hash=16 \
    option.OwnBook=false \
  -openings "file=$BOOK" format=epd order=sequential \
  -rounds "$ROUNDS" \
  -games 2 \
  -concurrency "$CONC" \
  -output format=fastchess \
  -pgnout "file=$OUT/${TAG}.pgn" notation=uci min=true \
  > "$OUT/${TAG}.txt" 2>&1
echo EXIT:$? >> "$OUT/${TAG}.txt"
