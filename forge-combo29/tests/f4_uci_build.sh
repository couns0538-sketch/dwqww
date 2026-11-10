#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-f4-uci}
f4=${2:-1}
"${CXX:-g++-14}" -std=c++20 -O1 -g -pthread -static-libstdc++ -ffp-contract=off -fno-fast-math \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -DFORGE_FIX_SMP_EXCEPTIONS="$f4" -I"$root/include" "$root/tests/f4_uci_inject.cpp" \
  "$root"/src/*.cpp -Wl,--wrap=pthread_create \
  -Wl,--wrap=_ZN5forge8Searcher6searchENS_5BoardERKNS_12SearchLimitsEbNS0_8TTAccessE -o "$out"
