#!/usr/bin/env bash
# Cloud review reproduction. Requires x86-64-v4; no timing/Elo claim.
# Continuation4Weight stays at its default zero: no search experiment enabled.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-/tmp/forge-review-build}
mkdir -p "$out"
cxx=${CXX:-g++}
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -I"$root/include")
fixes=(-DFORGE_FIX_SMP_NODE_RESET=1 -DFORGE_FIX_SMP_FINAL_NODES=1 -DFORGE_FIX_SMP_STOP_LATCH=1
       -DFORGE_FIX_UCI_OPTION_CASE=1 -DFORGE_BOOK_LEGAL_REUSE=1 -DFORGE_SPD_NNUE_CASTLE_FUSE=1
       -DFORGE_FIX_ATTACKS_INIT_ONCE=1 -DFORGE_FIX_SMP_EXCEPTIONS=1
       -DFORGE_SPD_MATERIAL_CORRECTION_CACHE=1 -DFORGE_FIX_TT_DEPTH_OVERFLOW=1
       -DFORGE_EXPERIMENT_CONTINUATION4=1 -DFORGE_SPD_LEGAL_WITNESSES=1 -DFORGE_SPD_COMPACT_PAWN_CACHE=1
       -DFORGE_SPD_TT_REPLACE_CACHE=1 -DFORGE_SPD_PICKER_SELF_SWAP_GUARD=1
       -DFORGE_SPD_WEAK_QUEEN_MASK=1 -DFORGE_SPD_EVAL_BITCOUNT_PREDICATES=1)
"$cxx" "${flags[@]}" "$root"/src/*.cpp -o "$out/default"
"$cxx" "${flags[@]}" "${fixes[@]}" "$root"/src/*.cpp -o "$out/enabled"
for variant in default enabled; do
  (cd "$out" && bash "$root/scripts/check_pins.sh" "$out/$variant") > "$out/$variant-pins.log"
  cp "$out/pins_out.txt" "$out/$variant-pins-raw.txt"
  python3 "$root/tests/review_evidence/uci_smoke.py" "$out/$variant" > "$out/$variant-uci.json"
done
python3 "$root/tests/uci_option_case.py" "$out/default" "$out/enabled"
