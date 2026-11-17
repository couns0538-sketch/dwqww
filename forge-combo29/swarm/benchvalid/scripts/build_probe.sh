#!/usr/bin/env bash
# Build the instrumented probes against the engine sources.
#   build_probe.sh <worktree-root> <out-binary> <probe.cpp> [extra cxx flags...]
# <worktree-root> is the directory that CONTAINS forge-combo29/ (i.e. the repo root
# of a `git worktree add ... 6b98f217` checkout).
#
# The -D values are copied verbatim from the CMake build's flags.make so the probe
# compiles under the same translation-unit settings as the real engine. A probe built
# with different defines is a different engine and its numbers do not transfer.
set -euo pipefail
SRC="${1:?worktree root}"
OUT="${2:?out binary}"
PROBE="${3:?probe source}"
shift 3
DEFS=(-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256
      -DFORGE_NNUE_WEIGHTS="\"${SRC}/forge-combo29/src/nnue_weights.inc\""
      -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2
      -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG)
mkdir -p "$(dirname "$OUT")"
/usr/bin/g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4 \
  "${DEFS[@]}" -I"${SRC}/forge-combo29/include" "$@" \
  "$PROBE" \
  "${SRC}/forge-combo29/src/board.cpp" "${SRC}/forge-combo29/src/search.cpp" \
  "${SRC}/forge-combo29/src/eval.cpp" "${SRC}/forge-combo29/src/eval_params.cpp" \
  "${SRC}/forge-combo29/src/nnue.cpp" "${SRC}/forge-combo29/src/nnue_v3.cpp" \
  "${SRC}/forge-combo29/src/bitboard.cpp" \
  -lpthread -o "$OUT"
