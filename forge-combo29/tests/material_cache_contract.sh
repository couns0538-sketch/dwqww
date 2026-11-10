#!/usr/bin/env bash
# Source-snapshot identity test. Reuse one exact build path and compiler command.
# Default tests isolated pre-S3 + original S3 + signature fix, not later patches.
set -euo pipefail
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
out=${1:-/tmp/forge-s3-contract}
mkdir -p "$out"
out=$(cd "$out" && pwd)
cxx=$(command -v "${CXX:-g++-14}")
base=$(git -C "$repo" rev-parse '25d8bd9^')
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude)
git -C "$repo" diff 25d8bd9^ 25d8bd9 -- forge-combo29/src/search.cpp forge-combo29/include/forge/search.hpp > "$out/original-s3.patch"
git -C "$repo" diff 6a945a4^ 6a945a4 -- forge-combo29/src/search.cpp forge-combo29/include/forge/search.hpp > "$out/s3-signature-fix.patch"
# Only remove the dedicated scratch source directory owned by this script.
rm -rf "$out/source"
mkdir "$out/source"
git -C "$repo" archive "$base" | tar -x -C "$out/source"
build() {
  (cd "$out/source/forge-combo29"; "$cxx" "${flags[@]}" src/*.cpp -o ../engine)
  cp "$out/source/engine" "$out/$1"
}
build pre-s3
(cd "$out/source"; git apply "$out/original-s3.patch"; git apply "$out/s3-signature-fix.patch")
build fixed-s3-off
cmp "$out/pre-s3" "$out/fixed-s3-off"
echo 'PASS: isolated fixed S3 default-off binary equals pre-S3 binary byte for byte'
(cd "$out/source/forge-combo29"; "$cxx" "${flags[@]}" -DFORGE_SPD_MATERIAL_CORRECTION_CACHE=1 src/*.cpp -o ../engine)
cp "$out/source/engine" "$out/fixed-s3-on"
python3 "$repo/forge-combo29/tests/equivalence_screen.py" "$out/pre-s3" "$out/fixed-s3-on" \
  --output "$out/material_cache_contract_equivalence.json" --depth 7
sha256sum "$out/pre-s3" "$out/fixed-s3-off" "$out/fixed-s3-on" > "$out/material_cache_contract_hashes.txt"
