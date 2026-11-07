#!/usr/bin/env bash
# t5_build_forge_probe.sh - OSS scout T5: build the R13 P6 tb_probe tool (Forge's own Syzygy reader) from
# build/t5/src_p6 (= lock d4f4312 + opus_r13/p6/syzygy_port.patch + tb_probe.cpp of P6 tip 4bf626eb), with the build
# line from the tb_probe.cpp header. g++ 15.2 (MSYS2 ucrt64). Refuses to overwrite.
set -euo pipefail
SRC=/c/opus_5h/oss_scout/build/t5/src_p6
OUT=/c/opus_5h/oss_scout/build/t5/forge
[ -e "$OUT/tb_probe.exe" ] && { echo "refusing: $OUT/tb_probe.exe exists"; exit 2; }
mkdir -p "$OUT"
export PATH=/c/msys64/ucrt64/bin:$PATH
cd "$SRC"
set -x
g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -static -Iinclude \
    tb_probe.cpp src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp \
    -o "$OUT/tb_probe.exe"
set +x
sha256sum "$OUT/tb_probe.exe"
