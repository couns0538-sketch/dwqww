#!/usr/bin/env bash
# Test match: IdeaA6 true vs IdeaA6 false, both S14, Threads 1, Hash 16, 20000 nodes.
# Openings are O then G (553). games 2 plays both colours. concurrency = cores - 1.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
OUT="forge-combo29/grok/$S"
EXE=/agent/repos/work/forge-combo29/build/forge
ROUNDS=${1:-553}
cat "$OUT/O.fens" "$OUT/G.epd" > "$OUT/OG.epd"
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
{
  echo "exe $EXE"
  echo "sha256 $(sha256sum "$EXE" | awk '{print $1}')"
  echo "id name $(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{sub(/^id name /,""); print; exit}')"
  echo "rounds $ROUNDS"
  echo "games 2"
  echo "concurrency $CONC"
  echo "nodes 20000"
  echo "openings $OUT/OG.epd"
  echo "options both: Threads 1, Hash 16, S14"
  echo "A6on IdeaA6 true"
  echo "A6off IdeaA6 false"
} > "$OUT/match.meta"
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
  -openings file="$OUT/OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 \
  -concurrency "$CONC" \
  -pgnout file="$OUT/match.pgn" nodes=true \
  -output format=fastchess
