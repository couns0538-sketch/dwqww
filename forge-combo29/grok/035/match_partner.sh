#!/usr/bin/env bash
# Partner switch on versus off. My 300 R openings, both colours, 20000 nodes, S14.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
EXE=/tmp/forge-partner/forge
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
{
  echo "exe $EXE"
  echo "sha256 $SHA"
  echo "$IDNAME"
  echo "fastchess /tmp/fastchess/fastchess"
  echo "concurrency 3"
  echo "nodes 20000"
  echo "rounds 300 games 2"
  echo "openings inputs/r300.fens"
  echo "on IdeaA4 true Divisor 8 Cap 256; off IdeaA4 false; S14 Threads 1 Hash 16"
} > match_partner.meta
/tmp/fastchess/fastchess \
  -engine cmd="$EXE" name=pon option.IdeaA4=true option.IdeaA4_Divisor=8 option.IdeaA4_Cap=256 \
  -engine cmd="$EXE" name=poff option.IdeaA4=false option.IdeaA4_Divisor=8 option.IdeaA4_Cap=256 \
  -each proto=uci nodes=20000 \
    option.LmrQuietBase=93 \
    option.LmrQuietDivisor=205 \
    option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 \
    option.LmrHistoryDivisor=5643 \
    option.NullMoveBase=5 \
    option.LmpBase=8 \
    option.HistoryPruneMultiplier=2220 \
    option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 \
    option.HistoryBonusMax=2212 \
    option.SingularDepth=6 \
    option.IirDepth=2 \
    option.NonPawnCorrection=true \
    option.Threads=1 \
    option.Hash=16 \
  -openings file=inputs/r300.fens format=epd order=sequential \
  -rounds 300 \
  -games 2 \
  -concurrency 3 \
  -pgnout file=match_partner.pgn notation=uci append=false \
  > match_partner.raw 2>&1
echo EXIT:$? >> match_partner.raw
