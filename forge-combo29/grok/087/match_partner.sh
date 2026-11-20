#!/usr/bin/env bash
# Partner switch, 300 of my R openings, both colours. My harness, their exe.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build/forge
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | awk '{print $1}')"
  echo "partner_commit dc16f1e927e57fee830653a35f9c59fdbede97fd"
  echo "rounds 300"
  echo "games 2"
  echo "concurrency $CONC"
  echo "nodes 20000"
  echo "openings $OUT/R.epd"
  echo "on IdeaA6 true"
  echo "off IdeaA6 false"
} > "$OUT/match_partner.meta"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=Pon option.IdeaA6=true \
  -engine cmd="$EXE" name=Poff option.IdeaA6=false \
  -each option.Threads=1 option.Hash=16 \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 \
        option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
        option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
        option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 \
        option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
        nodes=20000 \
  -openings file="$OUT/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 \
  -concurrency "$CONC" \
  -pgnout file="$OUT/match_partner.pgn" nodes=true \
  -output format=fastchess
