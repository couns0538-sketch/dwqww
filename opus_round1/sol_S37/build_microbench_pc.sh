#!/usr/bin/env bash
# S37: build tools/nnue_microbench.cpp with the PC lock recipe (MSYS2 ucrt64 g++ 15.2; -std=c++20 -O3 -DNDEBUG
# -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread) against the tree's own
# src/ (the 7 forge_core files of the box recipe minus uci.cpp; the microbench has its own main).
#   avx2   : exactly the lock recipe -> nnue::evaluate takes its __AVX2__ branch, GCC vectorises refresh/update.
#   scalar : nnue.cpp and the microbench compiled as S11's scalar NNUE build (build_pc_scalar_nnue.sh):
#            -U__AVX2__ -U__SSE__ -fno-tree-vectorize -fno-tree-slp-vectorize + scalar_nnue_prelude.hpp (undefines
#            MinGW's _M_X64/_M_AMD64) -> portable scalar branch, no packed float ops in forge::nnue::.
# The network is the tree's src/nnue_weights.inc (swap the file in a copied tree for another net).
# usage: build_microbench_pc.sh <src_dir> <out.exe> <avx2|scalar>      (absolute <out.exe>; objects in <out>.objs)
set -euo pipefail
SRC=$1; OUT=$2; MODE=$3
GPP=/c/msys64/ucrt64/bin/g++.exe
export PATH=/c/msys64/ucrt64/bin:$PATH
HERE=$(cd "$(dirname "$0")" && pwd)
OBJ="$OUT.objs"
mkdir -p "$OBJ"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude"
WARN="-Wall -Wextra -Wpedantic -Wconversion -Wshadow"
case "$MODE" in
  avx2) EXTRA="" ;;
  scalar) EXTRA="-U__AVX2__ -U__SSE__ -fno-tree-vectorize -fno-tree-slp-vectorize -include $HERE/scalar_nnue_prelude.hpp" ;;
  *) echo "mode must be avx2 or scalar"; exit 2 ;;
esac
cd "$SRC"
for f in bitboard board book eval eval_params search; do
  nice -n 19 "$GPP" $FLAGS -c "src/$f.cpp" -o "$OBJ/$f.o"
done
nice -n 19 "$GPP" $FLAGS $EXTRA -c src/nnue.cpp -o "$OBJ/nnue.o"
nice -n 19 "$GPP" $FLAGS $WARN $EXTRA -c tools/nnue_microbench.cpp -o "$OBJ/nnue_microbench.o"
nice -n 19 "$GPP" $FLAGS -static "$OBJ/bitboard.o" "$OBJ/board.o" "$OBJ/book.o" "$OBJ/eval.o" "$OBJ/eval_params.o" \
  "$OBJ/nnue.o" "$OBJ/search.o" "$OBJ/nnue_microbench.o" -o "$OUT"
echo "built $OUT ($MODE) sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
echo "net: src/nnue_weights.inc sha256 $(sha256sum src/nnue_weights.inc | cut -d' ' -f1)"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $(objdump -d "$OUT" | grep -cE 'vfn?m(add|sub)' || true)"
objdump -d -C --no-show-raw-insn "$OUT" | awk '/^[0-9a-f]+ <forge::nnue::/ {p=1; next} /^[0-9a-f]+ </ {p=0} p' > "$OBJ/nnue_functions.dis"
echo "forge::nnue:: packed float ops (v?(add|sub|mul|min|max)ps): $(grep -cE '\sv?(add|sub|mul|div|min|max)ps\s' "$OBJ/nnue_functions.dis" || true)"
echo "forge::nnue:: scalar float ops (v?(add|sub|mul|min|max)ss): $(grep -cE '\sv?(add|sub|mul|div|min|max)ss\s' "$OBJ/nnue_functions.dis" || true)"
echo "forge::nnue:: ymm/zmm register uses: $(grep -cE '%[yz]mm' "$OBJ/nnue_functions.dis" || true)"
