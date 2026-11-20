#!/usr/bin/env bash
# Match of the partner binary, switch on versus off, on this seat's R openings.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/tmp/fastchess/fastchess
ROUNDS="$1"
OPEN="$2"
STEM="$3"
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -n 1)
{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "id_name $IDNAME"
  echo "fastchess $FC"
  echo "rounds $ROUNDS"
  echo "concurrency $CONC"
  echo "openings $OPEN"
  echo "nodes 20000"
  echo "partner seat 078 IdeaB8 true versus false"
} > "$OUT/${STEM}.meta"
"$FC" \
  -engine cmd="$EXE" name=B8on option.IdeaB8=true \
  -engine cmd="$EXE" name=B8off option.IdeaB8=false \
  -each proto=uci nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 \
    option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$OPEN" format=epd order=sequential \
  -rounds "$ROUNDS" -repeat -concurrency "$CONC" \
  -pgnout "file=$OUT/${STEM}.pgn" \
  > "$OUT/${STEM}.txt" 2>&1
echo "exit $?" >> "$OUT/${STEM}.txt"
