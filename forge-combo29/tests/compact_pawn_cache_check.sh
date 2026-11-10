#!/usr/bin/env bash
set -euo pipefail
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
out=${1:-/tmp/forge-compact-pawn}
mkdir -p "$out"
out=$(cd "$out" && pwd)
mkdir -p "$out/source"
git -C "$repo" archive 703562d301d7a52111fa218ce0311141baf3eeb7 -- forge-combo29/src forge-combo29/include | tar -x -C "$out/source"
source="$out/source/forge-combo29"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
       -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude)
for mode in 0 1; do
  mkdir -p "$out/$mode"
  (cd "$source"; "$cxx" "${flags[@]}" -DFORGE_SPD_COMPACT_PAWN_CACHE=$mode src/*.cpp -o "$out/$mode/forge")
  (cd "$source"; "$cxx" "${flags[@]}" -DFORGE_SPD_COMPACT_PAWN_CACHE=$mode \
    "$repo/forge-combo29/tests/compact_pawn_cache_unit.cpp" src/{board,bitboard,eval,eval_params}.cpp -o "$out/$mode/unit")
  "$out/$mode/unit" | tee "$out/$mode/unit.json"
  (cd "$out/$mode"; bash "$repo/forge-combo29/scripts/check_pins.sh" ./forge) | tee "$out/$mode/pins.log"
done
python3 - "$out/0/forge" <<'PY'
import hashlib,sys
h=hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()
assert h == '1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6',h
print('PASS default-off byte hash equals immutable lock:',h)
PY
python3 "$repo/forge-combo29/tests/equivalence_screen.py" "$out/0/forge" "$out/1/forge" \
  --output "$out/equivalence.json" --depth 7
(cd "$source"; "$cxx" "${flags[@]}" -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer \
  -DFORGE_SPD_COMPACT_PAWN_CACHE=1 "$repo/forge-combo29/tests/compact_pawn_cache_unit.cpp" \
  src/{board,bitboard,eval,eval_params}.cpp -o "$out/unit-sanitize")
ASAN_OPTIONS=detect_leaks=0 "$out/unit-sanitize" | tee "$out/unit-sanitize.json"
sha256sum "$out/0/forge" "$out/1/forge" "$out/unit-sanitize" > "$out/hashes.txt"
