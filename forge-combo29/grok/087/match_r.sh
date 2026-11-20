#!/usr/bin/env bash
# Second match of this seat's patch: 300 R openings, both colours, 600 games.
# Used when the partner has no idea.patch.txt. Same settings as match.sh.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | awk '{print $1}')"
  echo "rounds 300"
  echo "games 2"
  echo "concurrency $CONC"
  echo "nodes 20000"
  echo "openings $OUT/R.epd"
  echo "A6on IdeaA6 true"
  echo "A6off IdeaA6 false"
} > "$OUT/match_r.meta"
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=A6on option.IdeaA6=true \
  -engine cmd="$EXE" name=A6off option.IdeaA6=false \
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
  -pgnout file="$OUT/match_r.pgn" nodes=true \
  -output format=fastchess
