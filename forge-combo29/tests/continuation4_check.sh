#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-continuation4}
mkdir -p "$out"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -I"$root/include")
for speed in 0 1; do
 for experiment in 0 1; do
  "$cxx" "${flags[@]}" -DFORGE_SEARCH_SPEED2=$speed -DFORGE_EXPERIMENT_CONTINUATION4=$experiment "$root"/src/*.cpp -o "$out/s${speed}-e${experiment}"
 done
done
for speed in 0 1; do
 "$cxx" "${flags[@]}" -DFORGE_SEARCH_SPEED2=$speed -DFORGE_EXPERIMENT_CONTINUATION4=1 \
  "$root/tests/continuation4_unit.cpp" "$root"/src/{bitboard,board,book,eval,eval_params,nnue}.cpp -o "$out/unit-$speed"
 "$out/unit-$speed"
done
"$cxx" "${flags[@]}" "$root/tests/continuation4_pv.cpp" "$root"/src/{bitboard,board}.cpp -o "$out/pv-validator"
for speed in 0 1; do
 for experiment in 0 1; do
  mode=s${speed}-e${experiment}
  mkdir -p "$out/$mode-pins"
  (cd "$out/$mode-pins" && bash "$root/scripts/check_pins.sh" "$out/$mode") | tee "$out/$mode-pins.log"
 done
done
python3 "$root/tests/continuation4_check.py" "$out"

for speed in 0 1; do
 PYTHONDONTWRITEBYTECODE=1 python3 "$root/tests/continuation4_option_order.py" "$out/s${speed}-e0" "$out/s${speed}-e1"
done
