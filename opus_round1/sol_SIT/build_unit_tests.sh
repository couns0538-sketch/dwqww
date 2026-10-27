#!/usr/bin/env bash
# S-IT follow-up: build tests/intended_threefold_tests.cpp with the box flags (MSYS2 ucrt64 g++ 15.2, -O3 -DNDEBUG,
# znver5, FMA contraction off, static) from per-TU objects, one compile at a time at nice 19.
# usage: build_unit_tests.sh <tree> <obj_dir> <out_exe> [<tree-relative TU to force-recompile>...]
#   Missing objects are compiled from <tree>; named TUs are always recompiled.
set -euo pipefail
TREE=$1; OBJ=$2; OUT=$3; shift 3
GPP=/c/msys64/ucrt64/bin/g++.exe
export PATH=/c/msys64/ucrt64/bin:$PATH
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread"
mkdir -p "$OBJ"
for f in src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp \
         tests/intended_threefold_tests.cpp; do
  o="$OBJ/$(basename "$f" .cpp).o"
  force=0
  for n in "$@"; do [ "$n" = "$f" ] && force=1; done
  if [ ! -f "$o" ] || [ $force = 1 ]; then
    echo "compile $TREE/$f"
    nice -n 19 "$GPP" $FLAGS -I"$TREE/include" -c "$TREE/$f" -o "$o"
  fi
done
nice -n 19 "$GPP" $FLAGS -static "$OBJ"/*.o -o "$OUT"
echo "linked $OUT"
