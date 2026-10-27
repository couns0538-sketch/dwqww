#!/usr/bin/env bash
# PC lock recipe (b/tools/build_pc.sh: MSYS2 ucrt64 g++ 15.2, same flags, same 8 files) with ONE change:
# src/nnue.cpp is compiled for the portable scalar NNUE path. -U__AVX2__ -U__SSE__ (plus the forced include
# scalar_nnue_prelude.hpp, which undefines MinGW's _M_X64/_M_AMD64) select the #else
# branch of nnue::evaluate (no AVX2/SSE intrinsics) and -fno-tree-vectorize -fno-tree-slp-vectorize stop
# GCC from re-vectorising the accumulator loops. The other 7 files are compiled exactly as build_pc.sh
# does. Correctness build for the scalar-vs-AVX2 node check only (not a speed build).
# usage: build_pc_scalar_nnue.sh <src_dir> <out.exe>      (absolute <out.exe>; objects next to it)
# Linux CI (box flags): GPP=g++-14 ARCH="-march=x86-64-v3 -mtune=znver5" LINK_STATIC= build_pc_scalar_nnue.sh ...
set -euo pipefail
SRC=$1; OUT=$2
GPP=${GPP:-/c/msys64/ucrt64/bin/g++.exe}
ARCH=${ARCH:--march=znver5}
LINK_STATIC=${LINK_STATIC--static}
export PATH=/c/msys64/ucrt64/bin:$PATH
OBJ="$(dirname "$OUT")/scalar_nnue_objs"
mkdir -p "$OBJ"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math $ARCH -pthread -Iinclude"
PRELUDE="$(cd "$(dirname "$0")" && pwd)/scalar_nnue_prelude.hpp"
SCALAR="-U__AVX2__ -U__SSE__ -fno-tree-vectorize -fno-tree-slp-vectorize -include $PRELUDE"
cd "$SRC"
for f in bitboard board book eval eval_params search uci; do
  nice -n 10 "$GPP" $FLAGS -c "src/$f.cpp" -o "$OBJ/$f.o"
done
nice -n 10 "$GPP" $FLAGS $SCALAR -c src/nnue.cpp -o "$OBJ/nnue.o"
echo "nnue.cpp macros with the scalar flags (need FORGE_NNUE_SSE 0; no __AVX2__, __SSE__, _M_X64, _M_AMD64, xmmintrin):"
"$GPP" $FLAGS $SCALAR -dM -E src/nnue.cpp | grep -E '^#define (__AVX2__|__SSE__|__SSE2__|FORGE_NNUE_SSE|_M_X64|_M_AMD64|_XMMINTRIN_H_INCLUDED|_IMMINTRIN_H_INCLUDED) ' || true
nice -n 10 "$GPP" $FLAGS $LINK_STATIC "$OBJ/bitboard.o" "$OBJ/board.o" "$OBJ/book.o" "$OBJ/eval.o" "$OBJ/eval_params.o" \
  "$OBJ/nnue.o" "$OBJ/search.o" "$OBJ/uci.o" -o "$OUT"
echo "built $OUT sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $(objdump -d "$OUT" | grep -cE 'vfn?m(add|sub)' || true)"
# Packed vs scalar float arithmetic inside forge::nnue:: functions of the linked exe.
objdump -d -C --no-show-raw-insn "$OUT" | awk '/^[0-9a-f]+ <forge::nnue::/ {p=1; print "FUNC " $0; next} /^[0-9a-f]+ </ {p=0} p' > "$OBJ/nnue_functions.dis"
echo "forge::nnue:: functions: $(grep -c '^FUNC' "$OBJ/nnue_functions.dis")"
echo "packed float arithmetic (v?(add|sub|mul|div|min|max)ps) in forge::nnue::: $(grep -cE '\sv?(add|sub|mul|div|min|max)ps\s' "$OBJ/nnue_functions.dis" || true)"
echo "scalar float arithmetic (v?(add|sub|mul|div|min|max)ss) in forge::nnue::: $(grep -cE '\sv?(add|sub|mul|div|min|max)ss\s' "$OBJ/nnue_functions.dis" || true)"
echo "ymm/zmm register uses in forge::nnue::: $(grep -cE '%[yz]mm' "$OBJ/nnue_functions.dis" || true)"
