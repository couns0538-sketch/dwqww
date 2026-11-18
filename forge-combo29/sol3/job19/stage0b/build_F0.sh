#!/usr/bin/env bash
set -euo pipefail
base=/workspace/work/sol3-job12/build_F
src=/workspace/work/sol3-job12/tree_F
new=/workspace/work/sol3-job19/build_F0
cmake=$(sed -n 's/^CMAKE_COMMAND:INTERNAL=//p' "$base/CMakeCache.txt")
flags=$(sed -n 's/^CMAKE_CXX_FLAGS:STRING=//p' "$base/CMakeCache.txt")
test "$(rg -o -- '-DFORGE_SPD_NNUE_ZMM=1' <<< "$flags" | wc -l)" -eq 1
flags0=${flags/-DFORGE_SPD_NNUE_ZMM=1/-DFORGE_SPD_NNUE_ZMM=0}
date -u +%FT%TZ
"$cmake" --version | head -1
c++ --version | head -1
dpkg-query -W g++-14 libstdc++6 libc6
printf 'Retained kF CXX flags %s\nNew kF0 CXX flags %s\n' "$flags" "$flags0"
"$cmake" -S "$src" -B "$new" -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "-DCMAKE_CXX_FLAGS=$flags0"
"$cmake" --build "$new" --parallel 4 --verbose
sha256sum "$new/forge"
date -u +%FT%TZ
