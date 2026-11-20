#!/usr/bin/env bash
# Test match: exe P, AspCappedReopen true vs false, S14, nodes 20000, openings O+G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DEST="$REPO/forge-combo29/grok/$S"
EXE=/tmp/forge-work/forge
FC=/tmp/fastchess/fastchess
OPEN="$DEST/openings_OG.epd"
OUT="$DEST/match_on_vs_off.txt"
META="$DEST/match_on_vs_off.meta"
WORKDIR=/tmp/match-009
mkdir -p "$WORKDIR"
cd "$WORKDIR"
rm -f config.json
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | awk '{print $1}')"
  echo "id_name $(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/id name /{print $2; exit}')"
  echo "fastchess $FC"
  echo "openings $OPEN"
  echo "games_expected 1106"
  echo "option setoption name LmrQuietBase value 93"
  echo "option setoption name LmrQuietDivisor value 205"
  echo "option setoption name LmrNoisyBase value 13"
  echo "option setoption name LmrNoisyDivisor value 333"
  echo "option setoption name LmrHistoryDivisor value 5643"
  echo "option setoption name NullMoveBase value 5"
  echo "option setoption name LmpBase value 8"
  echo "option setoption name HistoryPruneMultiplier value 2220"
  echo "option setoption name HistoryBonusQuadratic value 24"
  echo "option setoption name HistoryBonusLinear value 54"
  echo "option setoption name HistoryBonusMax value 2212"
  echo "option setoption name SingularDepth value 6"
  echo "option setoption name IirDepth value 2"
  echo "option setoption name NonPawnCorrection value true"
  echo "option setoption name Threads value 1"
  echo "option setoption name Hash value 16"
  echo "option setoption name IdeaS23_Margin value 13"
  echo "option setoption name IdeaS23_Decisive value 640"
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
      option.IdeaS23_Margin=13 option.IdeaS23_Decisive=640 \
    -openings file="$OPEN" format=epd order=sequential \
    -rounds 553 -repeat -concurrency 3 \
    -ratinginterval 200
  echo "fastchess_exit $?"
  echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT" 2>&1
echo "match_log_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$META"
