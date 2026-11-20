#!/usr/bin/env bash
# Partner 059 engine, AspCappedReopen true vs false, 300 R openings, both colours.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-partner/forge
FC=/tmp/fastchess/fastchess
OPEN="$DEST/R300.fen"
OUT="$DEST/partner_match.txt"
META="$DEST/partner_match.meta"
WORKDIR=/tmp/match-partner-059
mkdir -p "$WORKDIR"
cd "$WORKDIR"
rm -f config.json
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | awk '{print $1}')"
  echo "id_name $(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/id name /{print $2; exit}')"
  echo "fastchess $FC"
  echo "openings $OPEN"
  echo "games_expected 600"
  echo "engine on AspCappedReopen true"
  echo "engine off AspCappedReopen false"
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$META"
{
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$FC" \
    -engine cmd="$EXE" name=on option.AspCappedReopen=true \
    -engine cmd="$EXE" name=off option.AspCappedReopen=false \
    -each nodes=20000 option.Threads=1 option.Hash=16 \
      option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
      option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
      option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
      option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
      option.IirDepth=2 option.NonPawnCorrection=true \
    -openings file="$OPEN" format=epd order=sequential \
    -rounds 300 -repeat -concurrency 3 \
    -ratinginterval 300
  echo "fastchess_exit $?"
  echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT" 2>&1
echo "match_log_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$META"
