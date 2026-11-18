#!/usr/bin/env bash
set -euo pipefail
source_tree=$1
build_dir=$2
speed=$3
cmake=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
flags="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=$speed -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_NNUE_V3=1 -march=x86-64-v4"
date -u +%FT%TZ
"$cmake" --version | head -1
c++ --version | head -1
dpkg-query -W g++-14 libc6 libstdc++6
printf 'CMAKE_CXX_FLAGS=%s\n' "$flags"
"$cmake" -S "$source_tree" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=$flags"
"$cmake" --build "$build_dir" --parallel 4 --verbose
sha256sum "$build_dir/forge"
date -u +%FT%TZ
