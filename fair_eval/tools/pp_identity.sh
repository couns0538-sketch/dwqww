#!/usr/bin/env bash
# pp_identity.sh <pinned lock tree> <branch tree> - JOB D (own code). With every JOB D switch at 0 the eight
# units must preprocess to the same token stream as the pinned lock source (lock flags; blank lines ignored).
set -u
A="$1"; B="$2"
LM='/c/opus_5h/oss_scout/dl/llvm-mingw-20261104/x/llvm-mingw-20261104-ucrt-x86_64/bin'
export PATH="$LM:$PATH"
F="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=znver5 -pthread --sysroot=C:/msys64/ucrt64 -stdlib=libstdc++"
rc=0
for u in bitboard board book eval eval_params nnue search uci; do
  a=$(cd "$A" && clang++ $F -Iinclude -E -P src/$u.cpp 2>/dev/null | grep -v '^[[:space:]]*$' | sha256sum | cut -c1-16)
  b=$(cd "$B" && clang++ $F -Iinclude -E -P src/$u.cpp 2>/dev/null | grep -v '^[[:space:]]*$' | sha256sum | cut -c1-16)
  if [ "$a" = "$b" ] && [ "$a" != "e3b0c44298fc1c14" ]; then echo "$u IDENTICAL $a"; else echo "$u DIFFERENT $a $b"; rc=1; fi
done
exit $rc
