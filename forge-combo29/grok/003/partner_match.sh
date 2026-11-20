#!/usr/bin/env bash
# Partner binary, IdeaS38 on versus off, 300 R openings, both colours, 600 games.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
EXE=/agent/repos/partner/forge-combo29/build/forge
FC=/home/ubuntu/fastchess/fastchess
CORES=$(nproc)
CONC=$((CORES - 1))
[ "$CONC" -lt 1 ] && CONC=1
{
  echo "exe=$EXE"
  echo "sha256=$(sha256sum "$EXE" | awk '{print $1}')"
  echo "id_name=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -1)"
  echo "fastchess=$FC"
  echo "concurrency=$CONC"
  echo "openings=$DIR/R.epd"
  echo "opening_lines=$(wc -l < "$DIR/R.epd")"
  echo "engine1 IdeaS38 true"
  echo "engine2 IdeaS38 false"
} > "$DIR/partner_match.meta"
"$FC" \
  -engine cmd="$EXE" name=IdeaS38on option.IdeaS38=true \
  -engine cmd="$EXE" name=IdeaS38off option.IdeaS38=false \
  -each nodes=20000 option.Threads=1 option.Hash=16 \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$DIR/R.epd" format=epd order=sequential \
  -rounds 300 -games 2 -concurrency "$CONC" \
  -pgnout file="$DIR/partner_match.pgn" notation=uci \
  > "$DIR/partner_match.txt" 2>&1
echo "PARTNER_MATCH_EXIT:$?"
tail -n 20 "$DIR/partner_match.txt"
