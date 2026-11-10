#!/usr/bin/env bash
# Isolated strict-FP equivalence screen; not a timing or strength test.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-material-cache}
mkdir -p "$out"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -I"$root/include")
for mode in 0 1; do
  "$cxx" "${flags[@]}" -DFORGE_SPD_MATERIAL_CORRECTION_CACHE=$mode \
    "$root"/src/*.cpp -o "$out/material-cache-$mode"
done
"$cxx" "${flags[@]}" -DFORGE_SPD_MATERIAL_CORRECTION_CACHE=1 \
  "$root/tests/material_cache_unit.cpp" \
  "$root"/src/{bitboard,board,book,eval,eval_params,nnue}.cpp -o "$out/material-cache-unit"
"$out/material-cache-unit"
python3 "$root/tests/equivalence_screen.py" "$out/material-cache-0" "$out/material-cache-1" \
  --output "$out/material_cache_results.json" --depth 7
