#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'usage: bash %s <new scratch directory>\n' "$0" >&2
  exit 2
fi

baseline=/workspace/work/sol3-job4/tree_11
baseline_build=/workspace/work/sol3-job4/stage0/build_11.txt
cmake=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
recipe_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -- "$1"
work=$(cd -- "$1" && pwd)
tree="$work/tree"
build="$work/build"
mkdir "$tree"

exec > >(tee "$work/build.raw.txt") 2>&1
date -u +%FT%TZ
sha256sum "$baseline/CMakeLists.txt" "$baseline_build" "$recipe_dir/no-ndebug.diff"
cp -a "$baseline/." "$tree/"
patch_output=$(patch --batch --forward --directory "$tree" -p1 -F0 < "$recipe_dir/no-ndebug.diff")
printf '%s\n' "$patch_output"
if grep -Eiq 'offset|fuzz|reject' <<< "$patch_output"; then exit 1; fi

cxx_flags='-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_NNUE_V3=1 -march=x86-64-v4'
set -x
"$cmake" -S "$tree" -B "$build" -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/c++ "-DCMAKE_CXX_FLAGS=$cxx_flags" \
  -DCMAKE_CXX_FLAGS_RELEASE:STRING=-O3 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
set +x
if grep -n NDEBUG "$build/compile_commands.json"; then exit 1; fi

"$cmake" --build "$build" --parallel 4 --verbose | tee "$work/compiler.raw.txt"
compile_line=$(sed -n '/^\/usr\/bin\/c++ .* -c /{p;q;}' "$work/compiler.raw.txt")
test -n "$compile_line"
printf '%s\n' "$compile_line"
if printf '%s\n' "$compile_line" | grep -c NDEBUG; then exit 1; fi
sha256sum "$build/forge"
date -u +%FT%TZ
