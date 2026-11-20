#!/usr/bin/env bash
# Match exe P switch-true vs switch-false. Both S14, Threads 1, Hash 16, 20000 nodes.
# usage: run_match.sh OPENINGS OUT_PREFIX
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OPEN="$1"
TAG="$2"
EXE="/agent/repos/work/forge-combo29/build/forge"
FC="/tmp/fastchess/fastchess"
OUT="forge-combo29/grok/$S/${TAG}.txt"
PGN="forge-combo29/grok/$S/${TAG}.pgn"
ROUNDS=$(grep -cve '^$' "$OPEN")
# fastchess truncates the book to -rounds and -repeat sets two games per opening.
rm -f config.json "$PGN"
OPTS=(
  option.Hash=16
  option.Threads=1
  option.OwnBook=false
  option.EvalRule50Damp_Span=100
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
)
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "fastchess=$FC"
  echo "fastchess_sha256=$(sha256sum "$FC" | awk '{print $1}')"
  echo "openings=$OPEN"
  echo "rounds=$ROUNDS"
  echo "concurrency=3"
  date -u +%Y-%m-%dT%H:%M:%SZ
} > "forge-combo29/grok/$S/${TAG}.meta"
"$FC" \
  -engine cmd="$EXE" name=on proto=uci nodes=20000 option.EvalRule50Damp=true "${OPTS[@]}" \
  -engine cmd="$EXE" name=off proto=uci nodes=20000 option.EvalRule50Damp=false "${OPTS[@]}" \
  -openings file="$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency 3 \
  -pgnout file="$PGN" notation=uci \
  > "$OUT" 2>&1
echo EXIT:$? >> "$OUT"
echo "wrote $OUT"
