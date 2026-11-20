#!/usr/bin/env bash
# IdeaK8 on versus IdeaK8 off. S14, Threads 1, Hash 16, 20000 nodes, O then G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
EXE=/tmp/forge-builds/work/forge
FC=/tmp/fastchess/fastchess
cat "$D/O.fens" "$D/G.epd" > "$D/OG.epd"
CONC=$(( $(nproc) - 1 ))
ROUNDS=$(wc -l < "$D/OG.epd")
{
  echo "exe=$EXE"
  echo "fastchess=$FC"
  echo "concurrency=$CONC"
  echo "openings=$ROUNDS"
  echo "rounds=$ROUNDS"
  echo "games=2"
  date -u +%Y-%m-%dT%H:%M:%SZ
} > "$D/match_og.meta"
"$FC" \
  -engine cmd="$EXE" name=on proto=uci option.IdeaK8=true \
  -engine cmd="$EXE" name=off proto=uci option.IdeaK8=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        nodes=20000 \
  -openings file="$D/OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency "$CONC" \
  -pgnout file="$D/match_og.pgn" notation=uci nodes=true \
  > "$D/match_og.txt" 2> "$D/match_og.err"
echo "fastchess_exit=$?" >> "$D/match_og.meta"
date -u +%Y-%m-%dT%H:%M:%SZ >> "$D/match_og.meta"
tail -n 30 "$D/match_og.txt"
