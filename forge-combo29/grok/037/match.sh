#!/usr/bin/env bash
# Test match: IdeaA6 on vs IdeaA6 off. Same exe, S14, 20000 nodes, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
BOOK="$(pwd)/openings_OG.epd"
OUT="$(pwd)/match_on_off.txt"
PGN="$(pwd)/match_on_off.pgn"
sha256sum "$EXE" > match_on_off.meta
echo "exe=$EXE" >> match_on_off.meta
"$EXE" << 'EOF' >> match_on_off.meta
uci
quit
EOF
EACH=(
  nodes=20000
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
  option.Threads=1
  option.Hash=16
)
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on option.IdeaA6=true \
  -engine cmd="$EXE" name=off option.IdeaA6=false \
  -each "${EACH[@]}" \
  -openings file="$BOOK" format=epd order=sequential \
  -repeat \
  -rounds 553 \
  -concurrency 3 \
  -pgnout file="$PGN" \
  > "$OUT" 2>&1
echo "fastchess_exit=$?" >> match_on_off.meta
