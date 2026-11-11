#!/usr/bin/env bash
# plain_build.sh <gcc|clang> <out exe> [-DNAME=V ...] - JOB D (own code). One-step -O3 build of forge-combo29 with the
# lock defines and floating-point flags, no LTO, no PGO. For reference / cross-compiler diagnostic exes only; never timed.
set -eu
cc="$1"; out="$2"; shift 2
here="$(cd "$(dirname "$0")" && pwd)"; src="$here/../../forge-combo29"
defs="-DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1"
flags="-std=c++20 -O3 $defs $* -ffp-contract=off -fno-fast-math -march=znver5 -pthread -I$src/include"
mkdir -p "$(dirname "$out")"
if [ "$cc" = gcc ]; then
  export PATH="/c/msys64/ucrt64/bin:$PATH"
  g++ $flags -static "$src"/src/*.cpp -o "$out"
  echo "plain gcc $(g++ --version | head -1)"
else
  export PATH="/c/opus_5h/oss_scout/dl/llvm-mingw-20261104/x/llvm-mingw-20261104-ucrt-x86_64/bin:$PATH"
  clang++ $flags --sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc -fuse-ld=lld -static "$src"/src/*.cpp -o "$out" 2>&1 | grep -v "argument unused" || true
  echo "plain clang $(clang++ --version | head -1)"
fi
echo "built $out md5 $(md5sum "$out" | cut -c1-32) flags: $*"
