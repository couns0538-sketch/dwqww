#!/usr/bin/env bash
# Test match: exe P, DeadMaterial true vs false. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G, both colours. Concurrency = cores - 1.
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/home/ubuntu/build-work/forge
FC=/home/ubuntu/fastchess/fastchess
cat "$OUT/O.fens" "$OUT/G.epd" > "$OUT/OG.fens"
ROUNDS=$(wc -l < "$OUT/OG.fens")
CORES=$(nproc)
CONC=$((CORES - 1))
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "fastchess=$FC"
  echo "fastchess_sha256=$(sha256sum "$FC" | awk '{print $1}')"
  echo "rounds=$ROUNDS"
  echo "games_per_round=2"
  echo "concurrency=$CONC"
  echo "nodes=20000"
  echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/match_og.meta"
"$FC" \
  -engine cmd="$EXE" name=P-on option.DeadMaterial=true \
  -engine cmd="$EXE" name=P-off option.DeadMaterial=false \
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
  -openings file="$OUT/OG.fens" format=epd order=sequential \
  -games 2 -rounds "$ROUNDS" -concurrency "$CONC" -ratinginterval 100 \
  -pgnout file="$OUT/match_og.pgn" notation=uci nodes=true append=false \
  -log file="$OUT/match_og.log" level=info append=false engine=false \
  > "$OUT/match_og.out.txt" 2>&1
echo "MATCH_EXIT $?" >> "$OUT/match_og.out.txt"
echo "MATCH_DONE"
