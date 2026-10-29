#!/usr/bin/env bash
# Build and run tests/nnue_parity_tests.cpp (bit-for-bit NNUE parity against the verbatim AL1 s198 code, digest over
# every compared output) with the R5B box recipe for one kernel target, at BelowNormal, one thread.
# usage: [RECIPE=v3|znver5] parity_r5b.sh <src_dir> <out_dir> <name> [extra g++ flags, e.g. -DFORGE_NNUE_O2=1]
#        env PARITY_ARGS (default: the CTest arguments, --fens tests/data/nnue_selfplay_sample_916.txt)
# prints the test's kernel label, counts, digest and PASS/FAIL; exit status = the test's.
set -euo pipefail
SRC=$1; OUT=$2; NAME=$3; shift 3
export PATH=/c/msys64/ucrt64/bin:$PATH
case "${RECIPE:-v3}" in
  v3) ARCH="-march=x86-64-v3 -mtune=znver5" ;;
  znver5) ARCH="-march=znver5" ;;
  *) echo "parity_r5b: unknown RECIPE=${RECIPE}"; exit 1 ;;
esac
mkdir -p "$OUT"
EXE="$OUT/parity_$NAME.exe"
cd "$SRC"
nice -n 10 g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math $ARCH -pthread "$@" \
  -Iinclude tests/nnue_parity_tests.cpp src/nnue.cpp src/board.cpp src/bitboard.cpp -static -o "$EXE"
echo "parity $NAME: recipe ${RECIPE:-v3} flags [$*] exe sha256 $(sha256sum "$EXE" | cut -d' ' -f1)" \
  "FMA $(objdump -d "$EXE" | grep -cE 'vfn?m(add|sub)' || true)"
# shellcheck disable=SC2086
nice -n 10 "$EXE" ${PARITY_ARGS:---fens tests/data/nnue_selfplay_sample_916.txt}
