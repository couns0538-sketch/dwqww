#!/usr/bin/env bash
# Build forge without FORGE_* overrides and run the finding-10 checks
# under AddressSanitizer and UndefinedBehaviorSanitizer.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
source_dir=$(cd "$here/.." && pwd)
build_dir=${R4_BUILD_DIR:-/tmp/r4-10-asan}

CXX=g++ cmake -S "$source_dir" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_FLAGS="-g -fsanitize=address,undefined -fno-omit-frame-pointer" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build "$build_dir" -j"$(nproc)"

exec python3 -u "$here/check.py" "$build_dir/forge"
