#!/usr/bin/env bash
set -euo pipefail
base=$1
tree=$2
out=$3
cmake=$(sed -n 's/^CMAKE_COMMAND:INTERNAL=//p' "$base/CMakeCache.txt")
flags=$(sed -n 's/^CMAKE_CXX_FLAGS:STRING=//p' "$base/CMakeCache.txt")
test -n "$flags"
test -z "$(rg -o 'FORGE_SHADOW_EVAL' <<< "$flags" || true)"
date -u +%FT%TZ
"$cmake" --version | head -1
c++ --version | head -1
dpkg-query -W g++-14 libstdc++6 libc6
printf 'Retained baseline CMAKE_CXX_FLAGS %s\n' "$flags"
flags+=" -DFORGE_SHADOW_EVAL=1"
printf 'Shadow build CMAKE_CXX_FLAGS %s\n' "$flags"
"$cmake" -S "$tree" -B "$out" -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "-DCMAKE_CXX_FLAGS=$flags"
"$cmake" --build "$out" --parallel 4 --verbose
sha256sum "$out/forge"
date -u +%FT%TZ
