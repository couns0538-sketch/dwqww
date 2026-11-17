#!/usr/bin/env bash
# step0.sh EXE NET — FABLE_TO_swarm_7 Step 0: the eight bench numbers and three eval lines.
# A fresh process per line. Threads 1, Hash 16. Stops loudly on any refusal line.
set -u
EXE="$1"; NET="$2"
fail=0

run() { printf '%s\n' "$@" | "$EXE"; }

echo "=== CPU / compiler / march ==="
grep -m1 'model name' /proc/cpuinfo | sed 's/^/  /'
echo "  compiler: $(g++ --version | head -1)"
echo "  march: x86-64-v4 (CMake default); flags: -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1"
grep -o -m1 -E 'avx512f' /proc/cpuinfo >/dev/null && echo "  AVX-512F: present" || echo "  AVX-512F: ABSENT"

bench() { # label, setoption lines..., bench depth
  local label="$1"; shift
  local depth="$1"; shift
  local out
  out=$(run "uci" "$@" "bench $depth" "quit")
  if echo "$out" | grep -qE 'unknown option|invalid value|ERROR'; then
    echo "  $label: REFUSED -> $(echo "$out" | grep -E 'unknown option|invalid value|ERROR' | head -1)"
    fail=1; return
  fi
  local n
  n=$(echo "$out" | grep -o 'bench depth [0-9]* nodes [0-9]*' | grep -o 'nodes [0-9]*' | grep -o '[0-9]*')
  echo "  $label: nodes $n"
}

echo
echo "=== the eight bench numbers ==="
S14=( "setoption name LmrQuietBase value 93" "setoption name LmrQuietDivisor value 205"
      "setoption name LmrNoisyBase value 13" "setoption name LmrNoisyDivisor value 333"
      "setoption name LmrHistoryDivisor value 5643" "setoption name NullMoveBase value 5"
      "setoption name LmpBase value 8" "setoption name HistoryPruneMultiplier value 2220"
      "setoption name HistoryBonusQuadratic value 24" "setoption name HistoryBonusLinear value 54"
      "setoption name HistoryBonusMax value 2212" "setoption name SingularDepth value 6"
      "setoption name IirDepth value 2" "setoption name NonPawnCorrection value true" )
PC20=( "${S14[@]}" "setoption name CuckooRep value true" "setoption name HistRework value 2"
       "setoption name TtPruneV2 value true" "setoption name CorrHistV2 value true"
       "setoption name MateAlphaGuard value true" "setoption name OwnBook value false" )
NETOPT=( "setoption name NNUEArchFile value $NET" "setoption name NNUEArch value true" )

bench "no net, no setoption            b11" 11
bench "no net, no setoption            b13" 13
bench "PC20, no net                   b11" 11 "${PC20[@]}"
bench "PC20, no net                   b13" 13 "${PC20[@]}"
bench "test net only                  b11" 11 "${NETOPT[@]}"
bench "test net only                  b13" 13 "${NETOPT[@]}"
bench "PC20 then test net             b11" 11 "${PC20[@]}" "${NETOPT[@]}"
bench "PC20 then test net             b13" 13 "${PC20[@]}" "${NETOPT[@]}"

echo
echo "=== the net load line (PC20 + test net) ==="
run "uci" "${PC20[@]}" "${NETOPT[@]}" "isready" "quit" | grep -E 'NNUE v3 (loaded|active)|unknown option|invalid value|ERROR' | sed 's/^/  /'

echo
echo "=== the three eval lines (PC20 + test net) ==="
eval_of() { # label, position command
  local label="$1"; shift
  local out
  out=$(run "uci" "${PC20[@]}" "${NETOPT[@]}" "$@" "isready" "eval" "quit")
  if echo "$out" | grep -qE 'unknown option|invalid value|ERROR'; then
    echo "  $label: REFUSED"; fail=1; return
  fi
  echo "  $label: $(echo "$out" | grep 'info string eval' | tail -1)"
}
eval_of "startpos           " "position startpos"
eval_of "italian (2 3)      " "position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
eval_of "rook ending        " "position fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"

echo
[ "$fail" -eq 0 ] && echo "STEP 0: all lines produced, no refusal" || echo "STEP 0: FAILED — see refusals above"
exit "$fail"
