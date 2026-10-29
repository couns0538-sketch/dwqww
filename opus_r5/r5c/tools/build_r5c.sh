#!/usr/bin/env bash
# R5C engine build (copy of R5B opus_r5/r5b/tools/build_r5b.sh) (MSYS2 ucrt64 g++ 15.2, direct g++ like the PC lock exe, static link). Two recipes:
#   RECIPE=v3 (default) = the job-spec flags: -march=x86-64-v3 -mtune=znver5 (also the Linux box reference flags
#                         in the lock archive's 2_build/BUILD.md and R5A's build_r5a.sh)
#   RECIPE=znver5       = the PC lock exe recipe: -march=znver5 (2_build/BUILD.md "Windows", worktrees/b/tools/
#                         build_pc.sh, used by opus_r3/R3-1/tools/build_gate_exes.sh for the R3 gate exes)
# Common: -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -pthread.
# The 8 engine sources compile in parallel (JOBS, default 3 = the job's thread cap) at BelowNormal priority
# (Git Bash nice 10 = BELOW_NORMAL_PRIORITY_CLASS), then link in a fixed order.
# usage: [RECIPE=v3|znver5] build_r5c.sh <src_dir> <out_exe> [extra g++ flags, e.g. -DFORGE_NNUE_O2=1]   (absolute paths)
# prints: built <exe> sha256 <hex> / recipe line / FMA (vfmadd/vfmsub/vfnmadd) count: <n>   (the count must be 0)
set -euo pipefail
SRC=$1; OUT=$2; shift 2
export PATH=/c/msys64/ucrt64/bin:$PATH
case "${RECIPE:-v3}" in
  v3) ARCH="-march=x86-64-v3 -mtune=znver5" ;;
  znver5) ARCH="-march=znver5" ;;
  *) echo "build_r5b: unknown RECIPE=${RECIPE}"; exit 1 ;;
esac
OBJ="${OUT%.exe}.obj"
mkdir -p "$OBJ"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math $ARCH -pthread $*"
UNITS="bitboard board book eval eval_params nnue search uci"
cd "$SRC"
printf '%s\n' $UNITS | nice -n 10 xargs -P "${JOBS:-3}" -I{} sh -c "g++ $FLAGS -Iinclude -c src/{}.cpp -o '$OBJ/{}.o'"
OBJS=""
for u in $UNITS; do OBJS="$OBJS $OBJ/$u.o"; done
nice -n 10 g++ $FLAGS -static $OBJS -o "$OUT"
echo "built $OUT sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
echo "recipe ${RECIPE:-v3}: g++ $FLAGS -static"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $(objdump -d "$OUT" | grep -cE 'vfn?m(add|sub)' || true)"
