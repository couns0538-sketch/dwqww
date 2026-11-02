#!/usr/bin/env bash
# build_fastloader.sh OUT_DIR [extra g++ flags] - Opus R14-B: build forge_fastloader.dll with MinGW g++ 15.2 (the
# toolchain of the npt "setup" loader DLL, so std::shuffle / mt19937_64 behave the same), BelowNormal on CPUs 2-3
# (tools/lowrun.ps1: g++ and its children inherit the class and the mask).
# Never overwrites: OUT_DIR must not already hold a forge_fastloader.dll. Prints the DLL sha256.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=${1:?usage: build_fastloader.sh OUT_DIR [extra flags]}
shift
mkdir -p "$out"
if [ -e "$out/forge_fastloader.dll" ]; then
  echo "refusing to overwrite $out/forge_fastloader.dll" >&2
  exit 2
fi
src=$(cygpath -w "$here/forge_fastloader.cpp")
dll=$(cygpath -w "$out/forge_fastloader.dll")
lowrun=$(cygpath -w "$here/../tools/lowrun.ps1")
gxx='C:\msys64\ucrt64\bin\g++.exe'
# -march=znver5 -O3 like the old DLL's -march=native -O3 on this CPU (same FP contraction defaults); fixed random seed and
# no link timestamp so that two builds of the same source are byte-identical (pc1 = pc2).
flags="-std=gnu++20 -O3 -march=znver5 -DNDEBUG -Wall -Wextra -shared -static -frandom-seed=forge_fastloader -Wl,--exclude-libs,ALL -Wl,--no-insert-timestamp -Wl,--disable-auto-image-base $*"
PATH=/c/msys64/ucrt64/bin:$PATH powershell -NoProfile -File "$lowrun" -Mask 0xC -Priority BelowNormal -Exe "$gxx"   -ArgLine "$flags -o $dll $src"
test -s "$out/forge_fastloader.dll"
sha256sum "$out/forge_fastloader.dll"
