#!/usr/bin/env bash
# IdeaK9 true (cap 3) vs IdeaK9 false. S14, Threads 1, Hash 16, 20000 nodes.
# Openings O then G, 553 positions, both colours = 1106 games. Concurrency = cores - 1.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-release/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
CORES=$(nproc)
CONC=$((CORES - 1))
cat /tmp/kimi5/first200.fens /tmp/kimi5/set_G.epd > "$DIR/openings_og.epd"
FC=/tmp/fastchess/fastchess
OUT="$DIR/match_og.txt"
PGN="$DIR/match_og.pgn"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "fastchess=$FC"
  echo "fastchess_sha=$(sha256sum "$FC" | awk '{print $1}')"
  echo "concurrency=$CONC"
  echo "cores=$CORES"
  echo "openings=$DIR/openings_og.epd"
  echo "opening_lines=$(wc -l < "$DIR/openings_og.epd")"
  echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$DIR/match_og.meta"
"$FC" \
  -engine cmd="$EXE" name=on option.IdeaK9=true option.IdeaK9_Cap=3 \
  -engine cmd="$EXE" name=off option.IdeaK9=false \
  -each nodes=20000 proto=uci option.Hash=16 option.Threads=1 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/openings_og.epd" format=epd order=sequential \
  -rounds 553 -repeat -concurrency "$CONC" \
  -pgnout file="$PGN" \
  > "$OUT"
echo "finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DIR/match_og.meta"
tail -n 30 "$OUT"
