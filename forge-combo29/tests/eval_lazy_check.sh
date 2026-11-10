#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-eval-lazy}
mkdir -p "$out"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -DFORGE_FIX_SMP_NODE_RESET=1 -DFORGE_FIX_SMP_FINAL_NODES=1 -DFORGE_FIX_SMP_STOP_LATCH=1
       -DFORGE_FIX_UCI_OPTION_CASE=1 -DFORGE_BOOK_LEGAL_REUSE=1 -DFORGE_SPD_NNUE_CASTLE_FUSE=1
       -DFORGE_FIX_ATTACKS_INIT_ONCE=1 -DFORGE_FIX_SMP_EXCEPTIONS=1
       -DFORGE_SPD_MATERIAL_CORRECTION_CACHE=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -I"$root/include")
sources=("$root/tests/eval_lazy_audit.cpp" "$root"/src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp)
"$cxx" "${flags[@]}" -O3 "${sources[@]}" -o "$out/eval-lazy"
for seed in 3886096422 20261110 305419896; do
  "$out/eval-lazy" "$seed"
done | tee "$out/eval_lazy_release.jsonl"
"$cxx" "${flags[@]}" -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all \
  -fno-omit-frame-pointer "${sources[@]}" -o "$out/eval-lazy-sanitize"
# LeakSanitizer does not run under this environment's ptrace; ASan/UBSan remain on.
ASAN_OPTIONS=detect_leaks=0 "$out/eval-lazy-sanitize" 3886096422 | tee "$out/eval_lazy_sanitize.jsonl"
