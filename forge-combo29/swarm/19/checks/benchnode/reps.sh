#!/usr/bin/env bash
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
echo "rep bench reg nodes time_ms"
for rep in 1 2 3; do
for b in 11 13 16; do
  for regime in S14 PC20; do
    if [ "$regime" = "S14" ]; then OPTS="$S14"; EXE="$BASE"; else OPTS="$PC20"; EXE="$PC"; fi
    OUT=$({ echo "$OPTS"; echo isready; echo "bench $b"; echo quit; } | "$EXE" 2>&1)
    N=$(echo "$OUT" | grep -oE "nodes [0-9]+" | tail -1 | awk '{print $2}')
    T=$(echo "$OUT" | grep -oE "time [0-9]+" | tail -1 | awk '{print $2}')
    echo "$rep $b $regime $N $T"
  done
done
done
