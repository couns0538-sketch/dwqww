#!/usr/bin/env bash
# Build Forge exactly like the PC lock exe (MSYS2 ucrt64 g++ 15.2.0, direct g++, not CMake).
# usage: build_pc.sh <src_dir> <out_exe> [extra g++ flags...]   (pass an absolute <out_exe>)
set -euo pipefail
SRC=$1; OUT=$2; shift 2
GPP=/c/msys64/ucrt64/bin/g++.exe
export PATH=/c/msys64/ucrt64/bin:$PATH
cd "$SRC"
SRCS="src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp"
# extra sources (new modules) can be appended via FORGE_EXTRA_SRCS
SRCS="$SRCS ${FORGE_EXTRA_SRCS:-}"
nice -n 10 "$GPP" -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=${FORGE_HIDDEN:-256} -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude "$@" $SRCS -o "$OUT"
echo "built $OUT sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $(/c/msys64/ucrt64/bin/objdump.exe -d "$OUT" | grep -cE 'vfn?m(add|sub)' || true)"
