#!/usr/bin/env bash
# Build Forge by the recipe of the lock exe (forge-combo29/windows_build/BUILD_RECIPE.txt in the owner's repo):
# clang 23.1.5 from the official llvm-mingw release 20261104 (the clang++.exe here has the sha256 that the
# recipe records, d05fee2c...), ThinLTO, profile-guided (profile from the engine's own bench 11, 13, 16),
# -march=znver5, the strict floating-point flags. The lock's own measurement on this kind of CPU: the speed
# features in the source are worth about 2 % with GCC and about 10 % with this recipe.
# Differences from the recipe, all without influence on what the engine computes: no debug info and no PDB;
# the C++ library is the one given by FORGE_STDLIB (default: libstdc++ of the WinLibs GCC in tools/mingw64,
# as the recipe used GCC's library; "libc++" = llvm-mingw's own).
# The node counts must not change; the caller checks the pins.
#
#   build_forge_clang_pgo.sh <out_exe> [net.inc]
#   env: FORGE_SRC (default forge/r6), FORGE_DEFINES (default -DFORGE_MATE_ALPHA_GUARD=1), JOBS (default 8)
set -euo pipefail
OUT_EXE="$(cygpath -u "$1")"
NET="${2:-}"
if [ -n "$NET" ]; then NET="$(cygpath -u "$NET")"; fi
LOCK="${FORGE_SRC:-/c/nnue-lab/forge/r6}"
LLVM=/c/nnue-lab/tools/llvm/llvm-mingw-20261104-ucrt-x86_64
CXX="$LLVM/bin/clang++.exe"
PROFDATA="$LLVM/bin/llvm-profdata.exe"
HIDDEN=256
if [ -n "$NET" ]; then
  H="$(grep -o -m1 "NnueB1\[[0-9]*\]" "$NET" | grep -o "\[[0-9]*\]" | tr -d '[]' || true)"
  if [ -n "$H" ]; then HIDDEN="$H"; fi
fi
OUT_DIR="$(cd "$(dirname "$OUT_EXE")" 2>/dev/null && pwd || (mkdir -p "$(dirname "$OUT_EXE")" && cd "$(dirname "$OUT_EXE")" && pwd))"
WORK="$OUT_DIR/clang_src"
BUILD="$OUT_DIR/clang_build"
LOG="$OUT_DIR/build_clang.log"
rm -rf "$WORK" "$BUILD"
mkdir -p "$WORK" "$BUILD/gen" "$BUILD/use"
cp -r "$LOCK/src" "$LOCK/include" "$WORK/"
if [ -n "$NET" ]; then cp "$NET" "$WORK/src/nnue_weights.inc"; fi
W="$(cygpath -m "$WORK")"
B="$(cygpath -m "$BUILD")"
STDLIB="${FORGE_STDLIB:-libstdc++}"
if [ "$STDLIB" = "libstdc++" ]; then
  LIBFLAGS="--sysroot=C:/nnue-lab/tools/mingw64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc"
else
  LIBFLAGS="-stdlib=libc++"
fi
COMMON="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=$HIDDEN -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 \
-DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 \
-DFORGE_SPD_NNUE_ZMM=1 ${FORGE_DEFINES--DFORGE_MATE_ALPHA_GUARD=1} -ffp-contract=off -fno-fast-math \
-march=${FORGE_MARCH:-znver5} -pthread -I$W/include $LIBFLAGS -flto=thin"
LINK="-fuse-ld=lld -static -Wl,--no-insert-timestamp -Wl,--thinlto-jobs=${JOBS:-8}"
UNITS="$(cd "$WORK/src" && ls *.cpp | sed 's/\.cpp$//')"
{
  echo "compiler: $("$CXX" --version | head -n 1)"
  echo "flags: $COMMON"
} > "$LOG"
compile_all() {  # $1 = folder (gen/use), $2 = extra flags
  local pids=()
  for u in $UNITS; do
    "$CXX" $COMMON $2 -c "$W/src/$u.cpp" -o "$B/$1/$u.o" >> "$LOG" 2>&1 &
    pids+=($!)
    if [ "${#pids[@]}" -ge "${JOBS:-8}" ]; then wait "${pids[0]}"; pids=("${pids[@]:1}"); fi
  done
  for p in "${pids[@]}"; do wait "$p"; done
}
objs() { for u in $UNITS; do printf '%s ' "$B/$1/$u.o"; done; }
# step 1: instrumented build
compile_all gen "-fprofile-instr-generate"
"$CXX" $COMMON -fprofile-instr-generate $(objs gen) $LINK -o "$B/gen/forge_gen.exe" >> "$LOG" 2>&1
# step 2: the lock's profile workload (bench 11, 13, 16). With FORGE_V3_NET set (a FORGENN3 net file; needs a
# source with the v3 path and -DFORGE_NNUE_V3=1 in FORGE_DEFINES) the same benches run with that net active, so
# the profile covers the v3 evaluation: an exe built this way is meant for v3 nets only.
V3SET=""
if [ -n "${FORGE_V3_NET:-}" ]; then
  V3SET="setoption name NNUEArchFile value $(cygpath -m "$FORGE_V3_NET")"$'\n'"setoption name NNUEArch value true"$'\n'
  echo "profile workload with the v3 net $FORGE_V3_NET" >> "$LOG"
fi
# FORGE_PROFILE_OPTIONS="Name=value,Name=value" (2026-11-15): UCI options set for the profile run, so that code
# behind a switch is profiled the way it will be played. An exe whose profile was recorded with a switch OFF ran
# at half speed with the switch ON in an earlier job of this repo (fair-eval, 0.487 against 0.984): speed figures
# and clock matches of a switched-on engine need an exe built with the switches named here.
if [ -n "${FORGE_PROFILE_OPTIONS:-}" ]; then
  IFS=',' read -ra _popts <<< "$FORGE_PROFILE_OPTIONS"
  for _kv in "${_popts[@]}"; do
    V3SET="${V3SET}setoption name ${_kv%%=*} value ${_kv#*=}"$'\n'
  done
  echo "profile workload with the options $FORGE_PROFILE_OPTIONS" >> "$LOG"
fi
( cd "$BUILD/gen" && printf 'uci\n%sisready\nbench 11\nbench 13\nbench 16\nisready\nquit\n' "$V3SET" \
  | LLVM_PROFILE_FILE="$B/gen/forge.profraw" ./forge_gen.exe >> "$LOG" 2>&1 )
# Self-play profile (Opus 2026-11-17, tmp/opus_scratch/pgosp/DECLARATION.txt): with PGOSP_GAMES set, the profile
# ALSO holds PGOSP_GAMES self-play games ("go softnodes 2000", the loop's options for the v3 net) through
# PGOSP_DRIVER (pgo_selfplay.py); every engine process writes its own sp_<pid>.profraw, and all of them are merged
# with the bench profile. Without PGOSP_GAMES nothing here runs and the build is the one it always was.
SPF=""
if [ -n "${PGOSP_GAMES:-}" ]; then
  ( cd "$BUILD/gen" && LLVM_PROFILE_FILE="$B/gen/sp_%p.profraw" "$PGOSP_PY" -I -B "$PGOSP_DRIVER" "$PGOSP_CFG" "$(cygpath -m "$FORGE_V3_NET")" "$PGOSP_EPD" "$PGOSP_GAMES" "$B/gen/forge_gen.exe" >> "$LOG" 2>&1 < /dev/null )
  for f in "$BUILD"/gen/sp_*.profraw; do [ -s "$f" ] && SPF="$SPF $(cygpath -m "$f")"; done
  [ -n "$SPF" ] || { echo "pgosp: no self-play profile file was written" >> "$LOG"; exit 1; }
  echo "pgosp: self-play profile files:$SPF" >> "$LOG"
fi
"$PROFDATA" merge -o "$B/forge.profdata" "$B/gen/forge.profraw" $SPF >> "$LOG" 2>&1
# step 3: optimised build with the profile
compile_all use "-fprofile-instr-use=$B/forge.profdata"
"$CXX" $COMMON -fprofile-instr-use="$B/forge.profdata" $(objs use) $LINK -o "$B/use/forge.exe" >> "$LOG" 2>&1
cp "$BUILD/use/forge.exe" "$OUT_DIR/tmp_$(basename "$OUT_EXE")"
mv -f "$OUT_DIR/tmp_$(basename "$OUT_EXE")" "$OUT_EXE"
rm -rf "$BUILD" "$WORK"
echo "built $OUT_EXE (clang 23.1.5, ThinLTO + PGO, $STDLIB)"
