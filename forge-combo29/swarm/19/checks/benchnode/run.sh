#!/usr/bin/env bash
# 19-C54: does `bench` represent REAL positions for the NODE effect too?
# Measures bench 11/13/16 under S14 and under S14+PC20, both builds, and compares node ratios
# against the real-position ratio 0.9090 measured in 19-C53.
set -u
BASE=~/build_rel/forge
PC=~/pcbuild/build/forge
S14="setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true"
PC20="$S14
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false"

for b in 11 13 16; do
  for regime in S14 PC20; do
    if [ "$regime" = "S14" ]; then OPTS="$S14"; EXE="$BASE"; else OPTS="$PC20"; EXE="$PC"; fi
    { echo "$OPTS"; echo isready; echo "bench $b"; echo quit; } | "$EXE" > "raw_${b}_${regime}.txt" 2>&1
    N=$(grep -oE "nodes [0-9]+" "raw_${b}_${regime}.txt" | tail -1 | awk '{print $2}')
    T=$(grep -oE "time [0-9]+" "raw_${b}_${regime}.txt" | tail -1 | awk '{print $2}')
    echo "bench $b  $regime  nodes=$N  time=${T}ms  exe=$(basename $(dirname $EXE))"
  done
done
