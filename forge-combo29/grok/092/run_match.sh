#!/usr/bin/env bash
# Test match: HindsightDepth on versus off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings are O then G (553). -repeat plays both colours: 1106 games.
# Concurrency is cores minus 1.
set -u
S=$(cat ~/grok_seat.txt)
ROOT="$(cat ~/grok_repo.txt)"
DIR="$ROOT/forge-combo29/grok/$S"
EXE="$ROOT/../work/forge-combo29/build/forge"
# The work tree sits next to the clone. Prefer the absolute path recorded below if present.
if [ ! -x "$EXE" ]; then
  EXE=/agent/repos/work/forge-combo29/build/forge
fi
cd "$DIR"
cat /tmp/pos/first200.fens /tmp/pos/set_G.epd > openings_OG.epd
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
OPTS="nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
exec /tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on option.HindsightDepth=true \
  -engine cmd="$EXE" name=off option.HindsightDepth=false \
  -each $OPTS \
  -openings file="$DIR/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -repeat \
  -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout file="$DIR/match_on_off.pgn" notation=uci min=true \
  -recover
