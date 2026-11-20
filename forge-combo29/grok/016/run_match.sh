#!/usr/bin/env bash
# IdeaS13 on versus off. Both sides get S14, Threads 1, Hash 16, nodes per move.
# OwnBook is forced false: the embedded book defaults to true and would play
# the opening without search. Both sides get the same value.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
ROUNDS="${1:-553}"
OUT="$D/match_s13.txt"
PGN="$D/match_s13.pgn"
EXE=/agent/repos/work/build-rel/forge
BOOK="$D/match_OG.epd"
if [ ! -f "$BOOK" ]; then
  cat "$D/O_first200.fens" "$D/G_set.epd" > "$BOOK"
fi
rm -f "$PGN"
/home/ubuntu/fastchess/fastchess \
  -engine cmd="$EXE" name=s13on option.IdeaS13=true \
  -engine cmd="$EXE" name=s13off option.IdeaS13=false \
  -each option.Hash=16 option.Threads=1 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        option.OwnBook=false nodes=20000 \
  -openings file="$BOOK" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$PGN" notation=uci min=true \
  > "$OUT"
echo "WROTE $OUT"
tail -n 30 "$OUT"
