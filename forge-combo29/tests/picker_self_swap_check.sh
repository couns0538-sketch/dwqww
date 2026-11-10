#!/usr/bin/env bash
set -euo pipefail
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
out=${1:-/tmp/forge-picker-self-swap}
mkdir -p "$out/source"
out=$(cd "$out" && pwd)
git -C "$repo" archive fccd2c79c8367f577ebe4ed6d54b556555f94cce -- forge-combo29/src forge-combo29/include | tar -x -C "$out/source"
source="$out/source/forge-combo29"
cxx=${CXX:-g++-14}
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
       -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
       -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude -Isrc)
# Four relevant picker configurations, all compared to the exact locked policy.
for config in '1 0 2' '0 0 2' '1 1 2' '0 1 0'; do
  read -r speed prefix zero <<<"$config"
  tag="s${speed}-p${prefix}-z${zero}"
  (cd "$source"; "$cxx" "${flags[@]}" -DFORGE_SEARCH_SPEED2=$speed -DFORGE_SDK_BADCAP_PREFIX=$prefix \
    -DFORGE_SPD_NO_ZERO_MOVELISTS=$zero -DFORGE_SPD_PICKER_SELF_SWAP_GUARD=1 \
    "$repo/forge-combo29/tests/picker_self_swap_unit.cpp" src/{bitboard,board,book,eval,eval_params,nnue}.cpp -o "$out/unit-$tag")
  "$out/unit-$tag" | tee "$out/unit-$tag.json"
done
for speed in 1 0; do
  for guard in 0 1; do
    mkdir -p "$out/s${speed}-g${guard}"
    (cd "$source"; "$cxx" "${flags[@]}" -DFORGE_SEARCH_SPEED2=$speed -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
      -DFORGE_SPD_PICKER_SELF_SWAP_GUARD=$guard src/*.cpp -o "$out/s${speed}-g${guard}/forge")
  done
  python3 "$repo/forge-combo29/tests/equivalence_screen.py" "$out/s${speed}-g0/forge" "$out/s${speed}-g1/forge" \
    --output "$out/equivalence-speed${speed}.json" --depth 7
  if [[ $speed == 1 ]]; then
    for guard in 0 1; do
      (cd "$out/s1-g$guard"; bash "$repo/forge-combo29/scripts/check_pins.sh" ./forge) | tee "$out/s1-g$guard/pins.log"
    done
  fi
done
python3 - "$out/s1-g0/forge" <<'PY'
import hashlib,sys
h=hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()
assert h == '1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6',h
print('PASS default-off lock hash',h)
PY
(cd "$source"; "$cxx" "${flags[@]}" -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SDK_BADCAP_PREFIX=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PICKER_SELF_SWAP_GUARD=1 \
  "$repo/forge-combo29/tests/picker_self_swap_unit.cpp" src/{bitboard,board,book,eval,eval_params,nnue}.cpp -o "$out/unit-sanitize")
ASAN_OPTIONS=detect_leaks=0 "$out/unit-sanitize" | tee "$out/unit-sanitize.json"
