#!/usr/bin/env bash
# Latest combined TSan build: ten reviewed switches plus continuation4 compiled.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-smp-tsan-combined50}
mkdir -p "$out"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -O1 -g -pthread -fsanitize=thread -fno-omit-frame-pointer
       -fno-pie -no-pie -ffp-contract=off -fno-fast-math -march=x86-64-v3
       -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0
       -I"$root/include")
fixes=(-DFORGE_FIX_SMP_NODE_RESET=1 -DFORGE_FIX_SMP_FINAL_NODES=1 -DFORGE_FIX_SMP_STOP_LATCH=1
       -DFORGE_FIX_UCI_OPTION_CASE=1 -DFORGE_BOOK_LEGAL_REUSE=1 -DFORGE_SPD_NNUE_CASTLE_FUSE=1
       -DFORGE_FIX_ATTACKS_INIT_ONCE=1 -DFORGE_FIX_SMP_EXCEPTIONS=1
       -DFORGE_SPD_MATERIAL_CORRECTION_CACHE=1 -DFORGE_FIX_TT_DEPTH_OVERFLOW=1
       -DFORGE_EXPERIMENT_CONTINUATION4=1)
"$cxx" --version > "$out/compiler.txt"
"$cxx" "${flags[@]}" "${fixes[@]}" "$root"/src/*.cpp -o "$out/enabled"
sha256sum "$out/enabled" > "$out/binaries.sha256"
