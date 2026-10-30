#!/bin/sh
# Exact AL1 source snapshot identities are recorded in source-manifest.json.
set -eu
cd /tmp/astra-al1-full
/usr/bin/c++ -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -pthread -I/tmp/astra-al1-full/source/include /tmp/astra-al1-full/source/src/bitboard.cpp /tmp/astra-al1-full/source/src/board.cpp /tmp/astra-al1-full/source/src/book.cpp /tmp/astra-al1-full/source/src/eval.cpp /tmp/astra-al1-full/source/src/eval_params.cpp /tmp/astra-al1-full/source/src/nnue.cpp /tmp/astra-al1-full/source/src/search.cpp /tmp/astra-al1-full/source/src/uci.cpp -o /tmp/astra-al1-full/forge-al1
