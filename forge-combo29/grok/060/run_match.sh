#!/usr/bin/env bash
# Test match: IdeaS24 on versus IdeaS24 off, both the patched engine, S14, 20000 nodes.
# Openings are O then G. games 2 is both colours. rounds 1 does not repeat an opening.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="$PWD/forge-combo29/grok/$S"
EXE=/tmp/forge-build-work/forge
FC=/tmp/fastchess/fastchess
cat "$DIR/O.fens" "$DIR/G.epd" > "$DIR/OG.epd"
ROUNDS=$(wc -l < "$DIR/OG.epd")
EACH="proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
cd "$DIR"
"$FC" \
  -engine cmd="$EXE" name=s24on option.IdeaS24=true \
  -engine cmd="$EXE" name=s24off option.IdeaS24=false \
  -each $EACH \
  -openings file="$DIR/OG.epd" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency 3 \
  -pgnout file="$DIR/match.pgn" notation=uci min=true \
  > "$DIR/match_stdout.txt" 2>&1
echo MATCH_EXIT:$?
