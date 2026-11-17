#!/usr/bin/env bash
# Build the combo29 engine with UBSan+ASan. Every flag that changes what is
# checked, and every flag that changes the arithmetic, is on the command line
# so the build is reproducible from this file alone.
#
#   compiler   : /usr/bin/g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1)
#   LIBRARY_PATH is required in this image: /usr/bin/c++ is clang 18 with a
#   broken header path, and libstdc++ from gcc-13 is not on the default search
#   path.
set -euo pipefail
SRC=${1:?source dir (contains CMakeLists.txt, src/, include/)}
BUILD=${2:-/tmp/forge/build-ubsan}
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
SAN="-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g"
cmake -S "$SRC" -B "$BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
  -DFORGE_MARCH=x86-64-v4 \
  -DCMAKE_CXX_FLAGS="$SAN" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=undefined,address"
cmake --build "$BUILD" -j4
echo "--- resolved flags ---"
grep -E '^CXX_FLAGS|^CXX_DEFINES' "$BUILD/CMakeFiles/forge.dir/flags.make"
