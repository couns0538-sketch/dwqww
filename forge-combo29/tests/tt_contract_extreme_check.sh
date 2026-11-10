#!/usr/bin/env bash
# Reproduce the known LOW public-API depth overflow; nonzero is expected before fix.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-tt-extreme}
mkdir -p "$out"
cxx=${CXX:-g++-14}
status=0
for notls in 0 1; do
  "$cxx" -std=c++20 -O1 -g -pthread -fsanitize=undefined -fno-sanitize-recover=undefined \
    -fno-omit-frame-pointer -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 \
    -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -DFORGE_SPD_TT_NOTLS="$notls" \
    -I"$root/include" "$root/tests/tt_contract_test.cpp" \
    "$root"/src/{search,board,bitboard,eval,eval_params,nnue}.cpp -o "$out/tt-$notls"
  if "$out/tt-$notls" extreme > "$out/extreme-$notls.log" 2>&1; then
    echo "NOTLS=$notls extreme depth admitted and clamped without UBSan diagnostic"
  else
    code=$?
    echo "NOTLS=$notls failed with exit=$code"
    status=1
  fi
  cat "$out/extreme-$notls.log"
done
exit "$status"
