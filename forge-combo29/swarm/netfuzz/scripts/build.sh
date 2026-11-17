#!/usr/bin/env bash
# Build the loader probe against the engine sources, in two arms.
#
#   scripts/build.sh <forge-combo29 dir> <outdir>
#
# arm 1  rel   : -O2 release, the same flags as the engine build (march x86-64-v4)
# arm 2  asan  : -O1 -fsanitize=address,undefined -fno-sanitize-recover=all
#
# Both compile every engine source except uci.cpp (it owns main()), so the probe
# links the real loader, the real kernels and the real board.
set -euo pipefail

ENGINE="$(cd "${1:?engine dir}" && pwd)"
OUT="${2:?out dir}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"

SRCS=()
for f in "$ENGINE"/src/*.cpp; do
  case "$(basename "$f")" in
    uci.cpp) continue ;;   # provides main()
  esac
  SRCS+=("$f")
done
SRCS+=("$HERE/loadprobe.cpp")

COMMON=(-std=c++20 -DFORGE_NNUE_V3=1 -DFORGE_NNUE_HIDDEN=256
        -DFORGE_NNUE_WEIGHTS="\"$ENGINE/src/nnue_weights.inc\""
        -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2
        -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1
        -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1
        -I"$ENGINE/include" -pthread)

echo "== arm rel"
g++ "${COMMON[@]}" -O2 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
    "${SRCS[@]}" -o "$OUT/loadprobe_rel"
echo "== arm asan"
g++ "${COMMON[@]}" -O1 -g -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
    -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer \
    "${SRCS[@]}" -o "$OUT/loadprobe_asan"

echo "built:"
ls -la "$OUT"/loadprobe_rel "$OUT"/loadprobe_asan
