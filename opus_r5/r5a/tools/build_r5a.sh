#!/usr/bin/env bash
# R5A engine build, PC lock recipe flags from the job spec (as opus_r3/R3-1/tools/build_gate_exes.sh, MSYS2 ucrt64 g++):
#   -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256,
#   static link. The 8 engine sources compile in parallel (JOBS, default 3 = the job's thread cap) at BelowNormal
#   priority (Git Bash nice 10 = BELOW_NORMAL_PRIORITY_CLASS), then link in a fixed order.
# usage: build_r5a.sh <src_dir> <out_exe> [extra g++ flags...]      (absolute paths)
# prints: built <exe> sha256 <hex> / FMA (vfmadd/vfmsub/vfnmadd) count: <n>   (the count must be 0)
set -euo pipefail
SRC=$1; OUT=$2; shift 2
export PATH=/c/msys64/ucrt64/bin:$PATH
OBJ="${OUT%.exe}.obj"
mkdir -p "$OBJ"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 -pthread $*"
UNITS="bitboard board book eval eval_params nnue search uci"
cd "$SRC"
printf '%s\n' $UNITS | nice -n 10 xargs -P "${JOBS:-3}" -I{} sh -c "g++ $FLAGS -Iinclude -c src/{}.cpp -o '$OBJ/{}.o'"
OBJS=""
for u in $UNITS; do OBJS="$OBJS $OBJ/$u.o"; done
nice -n 10 g++ $FLAGS -static $OBJS -o "$OUT"
echo "built $OUT sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $(objdump -d "$OUT" | grep -cE 'vfn?m(add|sub)' || true)"
