#!/usr/bin/env bash
# pp_identity.sh - preprocessor identity of a default-OFF source change (own code, 2026-11-06).
# usage: bash pp_identity.sh <parent tree> <new tree> [-DNAME=V ...]
# Preprocesses every src/*.cpp of both trees with the lock's g++ flags (build_variants.ps1 line 143, -DNDEBUG,
# FORGE_EXPOSE_TUNABLES=1) plus the six trial_w6 lock switches and any extra -D given, drops blank lines (directive lines
# become blank lines; __LINE__ users would still differ), and compares the md5 per unit. Exit 0 = every unit identical.
set -u
[ $# -ge 2 ] || { echo "usage: pp_identity.sh <parent tree> <new tree> [-DNAME=V ...]"; exit 2; }
P="$1"; N="$2"; shift 2
GPP=/c/msys64/ucrt64/bin/g++.exe
SIX="-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1"
FLAGS="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -DFORGE_EXPOSE_TUNABLES=1 $SIX $*"
export PATH="/c/msys64/ucrt64/bin:$PATH"
bad=0
for f in "$P"/src/*.cpp; do
  u=$(basename "$f")
  [ -f "$N/src/$u" ] || { echo "MISSING $u in $N"; bad=1; continue; }
  a=$(cd "$P" && $GPP $FLAGS -Iinclude -E -P "src/$u" | grep -v '^[[:space:]]*$' | md5sum | cut -c1-32)
  b=$(cd "$N" && $GPP $FLAGS -Iinclude -E -P "src/$u" | grep -v '^[[:space:]]*$' | md5sum | cut -c1-32)
  if [ "$a" = "$b" ]; then echo "same  $u $a"; else echo "DIFF  $u $a $b"; bad=1; fi
done
for f in "$N"/src/*.cpp; do [ -f "$P/src/$(basename "$f")" ] || { echo "EXTRA $(basename "$f") in $N"; bad=1; }; done
[ $bad -eq 0 ] && echo "pp_identity: IDENTICAL ($*)" || echo "pp_identity: DIFFERENT ($*)"
exit $bad
