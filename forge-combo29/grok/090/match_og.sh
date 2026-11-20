#!/usr/bin/env bash
# Test match: IdeaK1 on versus IdeaK1 off. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G (553), both colours (1106 games). Concurrency = cores - 1.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
F="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-rel/forge
FC=/home/ubuntu/fastchess/fastchess
cd "$F"
cat first200.fens set_G.epd > openings_OG.epd
ROUNDS=$(wc -l < openings_OG.epd)
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "fastchess=$FC"
  echo "rounds=$ROUNDS"
  echo "concurrency=$CONC"
  echo "nodes=20000"
} > match_og.meta
"$FC" \
  -engine cmd="$EXE" name=IdeaK1on \
    option.IdeaK1=true option.IdeaK1_Margin=180 option.IdeaK1_DepthSlack=4 option.IdeaK1_MinDepth=5 \
  -engine cmd="$EXE" name=IdeaK1off \
    option.IdeaK1=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$F/openings_OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency "$CONC" \
  -ratinginterval 100 \
  -pgnout file="$F/match_og.pgn" notation=uci \
  > "$F/match_og.txt"
echo "match_og exit $?" >> "$F/match_og.meta"
