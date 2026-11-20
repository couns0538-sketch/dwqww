#!/usr/bin/env bash
# Test match: IdeaS10 on versus IdeaS10 off. Both get S14, Threads 1, Hash 16, 20000 nodes.
# Openings are O then G (553). games 2 plays both colours: 1106 games.
# Concurrency is cores minus 1.
set -u
S=$(cat ~/grok_seat.txt)
D="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-release/forge
FC=/tmp/fastchess/fastchess
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
cd "$D"
cat first200.fens set_G.epd > OG553.epd
{
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "exe $EXE"
  sha256sum "$EXE"
  echo "fastchess $FC"
  sha256sum "$FC"
  echo "concurrency $CONC"
  echo "cores $CORES"
  "$FC" \
    -engine cmd="$EXE" name=on option.IdeaS10=true \
    -engine cmd="$EXE" name=off option.IdeaS10=false \
    -each nodes=20000 option.Threads=1 option.Hash=16 \
      option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
      option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
      option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
      option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
      option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
      option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
    -openings file="$D/OG553.epd" format=epd order=sequential \
    -rounds 553 -games 2 \
    -concurrency "$CONC" \
    -pgnout file="$D/match_on_off.pgn" notation=uci nodes=true min=true \
    -ratinginterval 50
} > "$D/match_on_off.txt" 2> "$D/match_on_off.err"
echo "match_exit $?" >> "$D/match_on_off.txt"
