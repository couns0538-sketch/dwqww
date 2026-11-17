#!/usr/bin/env bash
# identity.sh BASE PATCHED NET — FABLE_TO_swarm_7 Step 2 identity check.
# A speed patch ships only if EVERY number is identical to the base. Any difference = drop it.
set -u
BASE="$1"; PATCHED="$2"; NET="$3"
fail=0

opts() { # prints the PC20 + net option lines
  cat <<'EOF'
setoption name LmrQuietBase value 93
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
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false
EOF
}

num() { # exe, bench depth -> node count
  local exe="$1" d="$2"
  { echo uci; opts; echo "setoption name NNUEArchFile value $NET"; echo "setoption name NNUEArch value true"; \
    echo isready; echo "bench $d"; echo quit; } | "$exe" \
    | grep -o "bench depth $d nodes [0-9]*" | grep -o '[0-9]*$'
}
evals() { # exe -> three eval values
  local exe="$1"
  { echo uci; opts; echo "setoption name NNUEArchFile value $NET"; echo "setoption name NNUEArch value true"; \
    echo isready
    echo "position startpos"; echo eval
    echo "position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"; echo eval
    echo "position fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"; echo eval
    echo quit; } | "$exe" | grep 'info string eval' | sed 's/.*total //'
}

echo "=== bench identity (PC20 + test net) ==="
for d in 11 13 16; do
  a=$(num "$BASE" $d); b=$(num "$PATCHED" $d)
  if [ "$a" = "$b" ]; then echo "  bench $d: $a == $b  OK"; else echo "  bench $d: $a vs $b  *** DIFFERS ***"; fail=1; fi
done

echo
echo "=== eval identity (three positions, PC20 + test net) ==="
ea=$(evals "$BASE"); eb=$(evals "$PATCHED")
if [ "$ea" = "$eb" ]; then echo "  identical: $(echo $ea | tr '\n' ' ')  OK"; else
  echo "  BASE   : $(echo $ea | tr '\n' ' ')"; echo "  PATCHED: $(echo $eb | tr '\n' ' ')"; echo "  *** DIFFERS ***"; fail=1
fi

echo
if [ "$fail" -eq 0 ]; then echo "IDENTITY: PASSED - every number identical"; else echo "IDENTITY: FAILED - this patch must be dropped"; fi
exit "$fail"
