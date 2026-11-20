#!/usr/bin/env bash
# Second match: IdeaK9 true vs false, 300 R openings, both colours, 600 games.
set -euo pipefail
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build-release/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
CORES=$(nproc)
CONC=$((CORES - 1))
FC=/tmp/fastchess/fastchess
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "fastchess=$FC"
  echo "fastchess_sha=$(sha256sum "$FC" | awk '{print $1}')"
  echo "concurrency=$CONC"
  echo "cores=$CORES"
  echo "openings=$DIR/R.fens"
  echo "opening_lines=$(wc -l < "$DIR/R.fens")"
  echo "started=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "why=partner 048 had no idea.patch.txt"
} > "$DIR/match_r.meta"
"$FC" \
  -engine cmd="$EXE" name=on option.IdeaK9=true option.IdeaK9_Cap=3 \
  -engine cmd="$EXE" name=off option.IdeaK9=false \
  -each nodes=20000 proto=uci option.Hash=16 option.Threads=1 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/R.fens" format=epd order=sequential \
  -rounds 300 -repeat -concurrency "$CONC" \
  -pgnout file="$DIR/match_r.pgn" \
  > "$DIR/match_r.txt"
echo "finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DIR/match_r.meta"
python3 "$DIR/read_match_result.py" "$DIR/match_r.txt"
