#!/usr/bin/env bash
# build_bareking_variants.sh : build four variants of the PC r15 source that differ ONLY in the two bare-king
# switches, to answer seat 21's 21-F22 question: which switch carries the depth-13 node explosion?
#
#   A: LMR_CAP=1, ONE_THREAD=0   (the PC's default)
#   B: LMR_CAP=0, ONE_THREAD=0   (reduction cap OFF)
#   C: LMR_CAP=1, ONE_THREAD=1   (one-thread switch ON)
#   D: LMR_CAP=0, ONE_THREAD=1   (both off/changed)
set -u
SRC=/agent/repos/pcbase/forge-combo29
BASE=/home/ubuntu/variants
mkdir -p "$BASE"

build() { # name  lmr  one
  local name="$1" lmr="$2" one="$3"
  local dir="$BASE/$name"
  rm -rf "$dir"; mkdir -p "$dir"
  echo "== building $name (LMR_CAP=$lmr ONE_THREAD=$one)"
  cmake -S "$SRC" -B "$dir" -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4 \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
        -DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_FIX_BARE_KING_LMR_CAP=$lmr -DFORGE_FIX_BARE_KING_ONE_THREAD=$one" \
        > "$dir/cmake.log" 2>&1 || { echo "CMAKE FAILED $name"; return 1; }
  make -C "$dir" -j4 > "$dir/make.log" 2>&1 || { echo "MAKE FAILED $name"; return 1; }
  echo -n "   exe sha256: "; sha256sum "$dir/forge" | awk '{print $1}'
}

build A 1 0
build B 0 0
build C 1 1
build D 0 1
echo "all variants built"
