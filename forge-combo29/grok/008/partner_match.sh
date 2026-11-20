#!/usr/bin/env bash
# Partner seat 058 switch, my harness. 300 R openings, both colours, 600 games.
set -u
SEAT="$(cat ~/grok_seat.txt)"
REPO="$(cat ~/grok_repo.txt)"
DIR="$REPO/forge-combo29/grok/$SEAT"
EXE="/agent/repos/partner/forge-combo29/build/forge"
FC="/tmp/fastchess/fastchess"
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=veto_on option.NullSeeVeto=true \
    option.NullSeeVeto_KingWorth=100000 option.NullSeeVeto_SeeMargin=0 \
  -engine cmd="$EXE" name=veto_off option.NullSeeVeto=false \
  -openings file="$DIR/R.epd" format=epd order=sequential \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -games 2 -rounds 300 -concurrency 3 \
  -pgnout file="$DIR/partner_match.pgn" nodes=true \
  -ratinginterval 100 \
  > "$DIR/partner_match.stdout.txt" 2> "$DIR/partner_match.stderr.txt"
echo "partner_match_exit=$?" | tee "$DIR/partner_match.exit.txt"
