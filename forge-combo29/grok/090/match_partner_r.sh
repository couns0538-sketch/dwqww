#!/usr/bin/env bash
# Partner patch, switch on versus off, 300 R openings, both colours, 600 games.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
F="$REPO/forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build-rel/forge
FC=/home/ubuntu/fastchess/fastchess
cd "$F"
ROUNDS=$(wc -l < set_R.fen)
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
  echo "openings=set_R.fen"
} > match_partner_r.meta
"$FC" \
  -engine cmd="$EXE" name=IdeaK1on \
    option.IdeaK1=true option.IdeaK1_Margin=120 \
  -engine cmd="$EXE" name=IdeaK1off \
    option.IdeaK1=false option.IdeaK1_Margin=120 \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$F/set_R.fen" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency "$CONC" \
  -ratinginterval 300 \
  -pgnout file="$F/match_partner_r.pgn" notation=uci \
  > "$F/match_partner_r.txt"
echo "match_partner_r exit $?" >> "$F/match_partner_r.meta"
