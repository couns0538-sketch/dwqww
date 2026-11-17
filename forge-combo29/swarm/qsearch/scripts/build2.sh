#!/bin/bash
set -e
src=$1; out=$2
g++ -std=c++20 -O2 -DNDEBUG -DFORGE_QS_TRACE=1 -DFORGE_NNUE_HIDDEN=256 \
 -DFORGE_NNUE_WEIGHTS="\"$src/src/nnue_weights.inc\"" -DFORGE_EXPOSE_TUNABLES=1 \
 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 \
 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 \
 -march=x86-64-v4 -I$src/include qs_probe2.cpp \
 $src/src/bitboard.cpp $src/src/board.cpp $src/src/book.cpp $src/src/eval.cpp \
 $src/src/eval_params.cpp $src/src/nnue.cpp $src/src/nnue_v3.cpp $src/src/search.cpp \
 -o $out -pthread
