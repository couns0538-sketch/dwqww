#!/usr/bin/env bash
# Layout control for PC NPS rows: re-link the object files of an existing build_r5b.sh exe in another unit order.
# Every function's code is the same as in the source exe (only placement and addresses change), so the NPS
# difference of the re-linked exe against the original is a pure code-layout effect: the "layout floor" that a
# switch row must clear before it says anything about the switch (R3-2Q: NOZERO -4.2 % on the PC = layout).
# usage: [RECIPE=v3|znver5] relink_layout.sh <source exe built by build_r5b.sh> <out exe> <unit order...>
#        e.g. relink_layout.sh off.exe off_relink.exe uci search nnue eval_params eval book board bitboard
# The source exe's object dir (<exe without .exe>.obj) must exist; the identity check is run separately.
set -euo pipefail
SRC_EXE=$1; OUT=$2; shift 2
export PATH=/c/msys64/ucrt64/bin:$PATH
case "${RECIPE:-v3}" in
  v3) ARCH="-march=x86-64-v3 -mtune=znver5" ;;
  znver5) ARCH="-march=znver5" ;;
  *) echo "relink_layout: unknown RECIPE=${RECIPE}"; exit 1 ;;
esac
OBJ="${SRC_EXE%.exe}.obj"
[ -d "$OBJ" ] || { echo "relink_layout: no object dir $OBJ"; exit 1; }
OBJS=""
for u in "$@"; do OBJS="$OBJS $OBJ/$u.o"; done
nice -n 10 g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math $ARCH -pthread \
  -static $OBJS -o "$OUT"
echo "relinked $OUT sha256 $(sha256sum "$OUT" | cut -d' ' -f1) from $OBJ order: $*"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $(objdump -d "$OUT" | grep -cE 'vfn?m(add|sub)' || true)"
