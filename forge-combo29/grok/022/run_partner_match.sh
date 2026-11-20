#!/usr/bin/env bash
# Partner switch, 300 R openings, both colours. usage: run_partner_match.sh TAG
# The on engine sets IdeaS27 true. Override with PARTNER_ON and PARTNER_OFF.
set -eu
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
TAG=$1
ON=${PARTNER_ON:-option.IdeaS27=true}
OFF=${PARTNER_OFF:-option.IdeaS27=false}
DIR="forge-combo29/grok/$S"
BOOK="$DIR/r.fens"
OUT="$DIR/partner_${TAG}/match_r.txt"
PGN="$DIR/partner_${TAG}/match_r.pgn"
mkdir -p "$DIR/partner_${TAG}"
stdbuf -oL -eL /tmp/fastchess/fastchess \
  -engine cmd=/tmp/forge-partner/forge name=on proto=uci "$ON" \
  -engine cmd=/tmp/forge-partner/forge name=off proto=uci "$OFF" \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=${BOOK}" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency 3 \
  -pgnout "file=${PGN}" \
  > "$OUT" 2>&1
echo "MATCH_EXIT $?" >> "$OUT"
