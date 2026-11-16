#!/usr/bin/env bash
# pc20_bench.sh EXE DEPTH [EXTRA] : one bench line under PC20, fresh process, refusal lines reported.
# PC20 = S14 (14 settings) + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
#        MateAlphaGuard true, OwnBook false.  Threads stays at its default of 1.
set -u
EXE="${1:?exe}"; DEPTH="${2:?depth}"; EXTRA="${3:-}"
S14=("LmrQuietBase 93" "LmrQuietDivisor 205" "LmrNoisyBase 13" "LmrNoisyDivisor 333"
     "LmrHistoryDivisor 5643" "NullMoveBase 5" "LmpBase 8" "HistoryPruneMultiplier 2220"
     "HistoryBonusQuadratic 24" "HistoryBonusLinear 54" "HistoryBonusMax 2212"
     "SingularDepth 6" "IirDepth 2" "NonPawnCorrection true")
PC=("CuckooRep true" "HistRework 2" "TtPruneV2 true" "CorrHistV2 true" "MateAlphaGuard true" "OwnBook false")
{
  echo uci; echo isready
  for s in "${S14[@]}" "${PC[@]}"; do echo "setoption name ${s% *} value ${s##* }"; echo isready; done
  [ -n "$EXTRA" ] && { echo "setoption name ${EXTRA% *} value ${EXTRA##* }"; echo isready; }
  echo "bench $DEPTH"; echo quit
} | "$EXE" 2>&1 | tr -d '\r' > /tmp/pc20b.$$.txt
refusals=$(grep -cE "unknown option|invalid value|ERROR" /tmp/pc20b.$$.txt || true)
nodes=$(grep -oE "bench depth $DEPTH nodes [0-9]+" /tmp/pc20b.$$.txt | sed 's/.*nodes //')
echo "depth=$DEPTH nodes=${nodes:-MISSING} refusals=$refusals"
[ "$refusals" != "0" ] && grep -E "unknown option|invalid value|ERROR" /tmp/pc20b.$$.txt | head -3
rm -f /tmp/pc20b.$$.txt
exit 0
