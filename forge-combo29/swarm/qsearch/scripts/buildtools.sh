#!/bin/bash
# Build the independent validation tools against an UNMODIFIED source tree.
#   ./buildtools.sh <src-tree> <outdir>
set -e
src=${1:?source tree}; out=${2:?output dir}
mkdir -p "$out"
COMMON="-std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
 -DFORGE_NNUE_WEIGHTS=\"$src/src/nnue_weights.inc\" -DFORGE_EXPOSE_TUNABLES=1
 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
 -march=x86-64-v4 -I$src/include"
LIBS="$src/src/bitboard.cpp $src/src/board.cpp $src/src/book.cpp $src/src/eval.cpp
 $src/src/eval_params.cpp $src/src/nnue.cpp $src/src/nnue_v3.cpp $src/src/search.cpp"
# classify.cpp is standalone: no engine sources needed.
g++ -std=c++17 -O2 classify.cpp -o "$out/classify"
# mate oracle + claim model link the engine's movegen only.
g++ $COMMON mateoracle.cpp $LIBS -o "$out/mateoracle" -pthread
g++ $COMMON claim_model.cpp $LIBS -o "$out/claim_model" -pthread
echo "built: $out/classify $out/mateoracle $out/claim_model"
