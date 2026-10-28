#!/usr/bin/env bash
# R3-1 self-play: builds the engine set of one stack head with the PC recipe (build_pc.sh: g++ 15.2 ucrt64, -O3,
# znver5, static, FMA off), one g++ at a time at nice 19. Names: opus_r3sp_<key>.exe (keys used by configs*.json).
# usage: build_engines.sh <stack worktree> <out dir> [<H512 net .inc>]
#   base        no switch                    o2          -DFORGE_NNUE_O2=1
#   nozero      -DFORGE_NOZERO_MOVE_BUFFERS=1 s13        -DFORGE_S13_TT_CHILD_PREFETCH=1 (+ UCI TtChildPrefetch)
#   speedstack  -DFORGE_SPEEDSTACK=1         lazyacc     -DFORGE_NNUE_LAZY_ACC=1 (+ UCI NnueLazyAcc)
#   prof        -DFORGE_PROF=1, FORGE_EXTRA_SRCS=src/profile.cpp (+ UCI Profile)
#   int16       -DFORGE_NNUE_INT16=1 (+ UCI NnueInt16)       initonce  -DFORGE_ATTACKS_INIT_ONCE=1 (S04fix)
#   allsw       every switch above
#   h512        -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS=<H512 net> -DFORGE_NNUE_INT16=1 (S-A4)
# Switches a head does not have yet are skipped (grep in src/ and include/). Prints sha256, FMA count, warnings.
set -euo pipefail
SRC=$1; OUT=$2; H512=${3:-}
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
mkdir -p "$OUT"
has() { grep -rqs "$1" "$SRC/src" "$SRC/include"; }
build() {   # key extra_srcs flags...
  local key=$1 extra=$2; shift 2
  echo "== $key extra_srcs='$extra' flags: $*"
  FORGE_EXTRA_SRCS="$extra" nice -n 19 bash "$T/build_pc.sh" "$SRC" "$OUT/opus_r3sp_$key.exe" "$@" > "$OUT/build_$key.log" 2>&1
  tail -2 "$OUT/build_$key.log"
  echo "warnings: $(grep -ci warning "$OUT/build_$key.log" || true)"
}
ALL=(-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_S13_TT_CHILD_PREFETCH=1 -DFORGE_SPEEDSTACK=1)
EXTRA_ALL=""
build base ""
build o2 "" -DFORGE_NNUE_O2=1
build nozero "" -DFORGE_NOZERO_MOVE_BUFFERS=1
build s13 "" -DFORGE_S13_TT_CHILD_PREFETCH=1
build speedstack "" -DFORGE_SPEEDSTACK=1
if has FORGE_NNUE_LAZY_ACC; then build lazyacc "" -DFORGE_NNUE_LAZY_ACC=1; ALL+=(-DFORGE_NNUE_LAZY_ACC=1); fi
if has FORGE_PROF; then build prof src/profile.cpp -DFORGE_PROF=1; ALL+=(-DFORGE_PROF=1); EXTRA_ALL=src/profile.cpp; fi
if has FORGE_NNUE_INT16; then build int16 "" -DFORGE_NNUE_INT16=1; ALL+=(-DFORGE_NNUE_INT16=1); fi
if has FORGE_ATTACKS_INIT_ONCE; then build initonce "" -DFORGE_ATTACKS_INIT_ONCE=1; ALL+=(-DFORGE_ATTACKS_INIT_ONCE=1); fi
build allsw "$EXTRA_ALL" "${ALL[@]}"
if [ -n "$H512" ] && has FORGE_NNUE_WEIGHTS; then
  build h512 "" -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512 "-DFORGE_NNUE_WEIGHTS=\"$H512\"" -DFORGE_NNUE_INT16=1
fi
