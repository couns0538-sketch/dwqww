#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out="${1:-/tmp/forge-legal-witness-engine}"
mkdir -p "$out"
out=$(cd "$out" && pwd)
flags=(-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1
 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -I"$root/include")
for witnesses in 0 1; do
 mkdir -p "$out/$witnesses"
 "${CXX:-g++-14}" "${flags[@]}" -DFORGE_SPD_LEGAL_WITNESSES="$witnesses" "$root"/src/*.cpp -o "$out/$witnesses/forge"
 (cd "$out/$witnesses" && bash "$root/scripts/check_pins.sh" "$out/$witnesses/forge") | tee "$out/$witnesses/pins.log"
done
python3 "$root/tests/equivalence_screen.py" "$out/0/forge" "$out/1/forge" --output "$out/equivalence.json"
sha256sum "$out/0/forge" "$out/1/forge"
