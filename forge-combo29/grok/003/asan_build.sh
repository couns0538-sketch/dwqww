#!/usr/bin/env bash
# AddressSanitizer + UndefinedBehaviorSanitizer build. Own folder. Not committed.
set -u
SRC="${1:-/agent/repos/work/forge-combo29}"
cd "$SRC"
rm -rf build-asan
cmake -S . -B build-asan -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build build-asan -j4
echo "NM_ASAN $(nm -C "$SRC/build-asan/forge" | grep -c __asan_)"
echo "EXE $SRC/build-asan/forge"
