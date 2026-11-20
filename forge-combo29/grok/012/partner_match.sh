#!/usr/bin/env bash
# Partner switch, my R openings, both colours. 300 openings, 600 games.
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/home/ubuntu/build-partner/forge
FC=/home/ubuntu/fastchess/fastchess
ROUNDS=$(wc -l < "$OUT/R.fens")
CORES=$(nproc)
CONC=$((CORES - 1))
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "fastchess=$FC"
  echo "rounds=$ROUNDS"
  echo "games_per_round=2"
  echo "concurrency=$CONC"
  echo "nodes=20000"
  echo "openings=$OUT/R.fens"
  echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/partner_match.meta"
"$FC" \
  -engine cmd="$EXE" name=P062-on option.DeadMaterial=true \
  -engine cmd="$EXE" name=P062-off option.DeadMaterial=false \
  -each nodes=20000 \
    option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
    option.IdeaP20_Corner=28 option.IdeaP20_King=12 \
  -openings file="$OUT/R.fens" format=epd order=sequential \
  -games 2 -rounds "$ROUNDS" -concurrency "$CONC" -ratinginterval 100 \
  -pgnout file="$OUT/partner_match.pgn" notation=uci nodes=true append=false \
  -log file="$OUT/partner_match.log" level=info append=false engine=false \
  > "$OUT/partner_match.out.txt" 2>&1
echo "MATCH_EXIT $?" >> "$OUT/partner_match.out.txt"
echo "PARTNER_MATCH_DONE"
