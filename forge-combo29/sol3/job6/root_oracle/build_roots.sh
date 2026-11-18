#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  printf 'usage: bash %s <scratch probe-or-control tree> <new output build directory>\n' "$0" >&2
  exit 2
fi

tree=$(realpath -e -- "$1")
build=$(realpath -m -- "$2")
[[ ! -e "$build" ]]
oracle=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cmake=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
cxx_flags='-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_NNUE_V3=1 -march=x86-64-v4'

date -u +%FT%TZ
sha256sum "$oracle/hlm_roots.cpp" "$oracle/CMakeLists.txt" "$tree/include/forge/hlm_probe.hpp" \
  "$tree/src/board.cpp" "$tree/src/bitboard.cpp" "$tree/CMakeLists.txt"
set -x
"$cmake" -S "$oracle" -B "$build" "-DFORGE_PROBE_TREE:PATH=$tree" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/c++ \
  "-DCMAKE_CXX_FLAGS=$cxx_flags" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
"$cmake" --build "$build" --target hlm_roots --parallel 2 --verbose
set +x
sha256sum "$build/hlm_roots"
date -u +%FT%TZ
