#!/usr/bin/env bash
# build_harness_o30.sh <scratch repo with the v2 port> <out dir> - builds the parity / walk harness v2_eval_o30 three
# times from a clean export of the port: AVX2 (x86-64-v3), SSE (x86-64-v2, no ymm), scalar (x86-64-v3 with
# -DFORGE_NNUE_V2_SCALAR=1). Same flags as the R14 harness builds (-O2 -ffp-contract=off -fno-fast-math -static).
# CPUs 0-1 at Idle through lowrun.ps1. Refuses an existing <out dir>.
set -euo pipefail
repo="$1"; out="$2"
A=$(cd "$(dirname "$0")" && pwd); T="$A/../tools"
[ -e "$out" ] && { echo "refusing: $out exists" >&2; exit 2; }
export PATH="/c/msys64/ucrt64/bin:$PATH"
bash "$T/export_src.sh" "$repo" "$out/src" >/dev/null
cp "$A/v2_eval_o30.cpp" "$out/src/v2_eval_o30.cpp"
cd "$out/src"
units="src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp"
common="-std=c++20 -O2 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -static -pthread -Iinclude v2_eval_o30.cpp $units"
for variant in avx2 sse scalar; do
  case $variant in
    avx2) flags="-march=x86-64-v3" ;;
    sse) flags="-march=x86-64-v2" ;;
    scalar) flags="-march=x86-64-v3 -DFORGE_NNUE_V2_SCALAR=1" ;;
  esac
  powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/lowrun.ps1")" -Mask 0x3 -Priority Idle \
    -Exe 'C:\msys64\ucrt64\bin\g++.exe' -ArgLine "$common $flags -o ../v2_eval_$variant.exe" > "../build_$variant.log" 2>&1 \
    || { tail -20 "../build_$variant.log"; exit 1; }
  echo "$variant: warnings $(grep -c 'warning:' ../build_$variant.log || true), sha256 $(sha256sum ../v2_eval_$variant.exe | cut -c1-16)"
done
echo "sse ymm instructions: $(objdump -d ../v2_eval_sse.exe | grep -c 'ymm' || true)"
