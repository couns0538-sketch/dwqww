#!/usr/bin/env bash
# Test match: IdeaS38 on vs off, S14, 20000 nodes, openings O+G, both colours.
set -u
S=$(cat ~/grok_seat.txt)
OUT="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
cd "$OUT"
P=/agent/repos/work/forge-combo29/build-release/forge
cat /tmp/first200.fens /tmp/set_G.epd > openings_OG.epd
echo "openings $(wc -l < openings_OG.epd)"
sha256sum "$P" | awk '{print $1}' > match_OG.exe.sha
{
  echo "exe=$P"
  echo "sha256=$(cat match_OG.exe.sha)"
  echo "concurrency=3"
  echo "nodes=20000"
  echo "threads=1"
  echo "hash=16"
  echo "switch_pair=on_vs_off"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > match_OG.meta
/tmp/fastchess/fastchess \
  -engine cmd="$P" name=on option.IdeaS38=true \
  -engine cmd="$P" name=off option.IdeaS38=false \
  -each proto=uci nodes=20000 \
        option.Threads=1 option.Hash=16 option.OwnBook=false option.Ponder=false \
        option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
        option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
        option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
        option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
        option.IirDepth=2 option.NonPawnCorrection=true \
  -openings file="$OUT/openings_OG.epd" format=epd order=sequential \
  -rounds 553 -games 2 \
  -concurrency 3 \
  -pgnout file="$OUT/match_OG.pgn" notation=uci min=true append=false \
  -config outname="$OUT/match_OG.config.json" \
  -ratinginterval 50 \
  > "$OUT/match_OG.fastchess.txt" 2>&1
echo "fastchess_exit=$?" >> match_OG.meta
echo DONE
