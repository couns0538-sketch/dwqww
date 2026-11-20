#!/usr/bin/env bash
# Partner 042's IdeaK3, on versus off. My R openings, both colours, 600 games.
set -u
S=$(cat ~/grok_seat.txt)
ROOT="$(cat ~/grok_repo.txt)"
DIR="$ROOT/forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build/forge
cd "$DIR"
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
OPTS="nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
exec /tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=on option.IdeaK3=true \
  -engine cmd="$EXE" name=off option.IdeaK3=false \
  -each $OPTS \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -repeat \
  -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout file="$DIR/partner_match_R.pgn" notation=uci min=true \
  -recover
