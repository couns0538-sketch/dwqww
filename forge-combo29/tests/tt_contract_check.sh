#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-tt-contract}
if (($#)); then shift; fi
extra_flags=("$@")
mkdir -p "$out"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -O1 -g -pthread -fno-omit-frame-pointer -fno-pie -no-pie
       -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256
       -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I"$root/include")
sources=("$root/tests/tt_contract_test.cpp" "$root/src/search.cpp" "$root/src/board.cpp"
         "$root/src/bitboard.cpp" "$root/src/eval.cpp" "$root/src/eval_params.cpp" "$root/src/nnue.cpp")
for notls in 0 1; do
  "$cxx" "${flags[@]}" "${extra_flags[@]}" -fsanitize=thread -DFORGE_SPD_TT_NOTLS="$notls" "${sources[@]}" -o "$out/tt-$notls"
  if TSAN_OPTIONS=halt_on_error=1:exitcode=66 "$out/tt-$notls" > "$out/notls-$notls.log" 2>&1; then
    cat "$out/notls-$notls.log"
  else
    code=$?
    cat "$out/notls-$notls.log"
    exit "$code"
  fi
done
