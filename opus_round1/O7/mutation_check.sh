#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that forge_nnue_pawn_pair_tests (with the engine
# for its UCI part) fails. usage (from the repository root):
#   opus_round1/O7/mutation_check.sh <scratch_dir> [mutation names...]   (default: all mutations)
# Environment: CXX (compiler), MUTATION_LINK_FLAGS (e.g. -static on MinGW), JOBS (default 1).
# The scratch copy and its build are reused by later calls, so the mutations can be run in several short parts.
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
shift
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
mkdir -p "$SRC"
cp -a "$ROOT/include" "$ROOT/src" "$ROOT/tests" "$ROOT/tools" "$ROOT/bench" "$ROOT/CMakeLists.txt" "$SRC/"
if [ ! -f "$BUILD/build.ninja" ]; then
  cmake -S "$SRC" -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=${CXX:-g++}" \
    "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
    ${MUTATION_LINK_FLAGS:+"-DCMAKE_EXE_LINKER_FLAGS=$MUTATION_LINK_FLAGS"} > "$SCRATCH/configure.log" 2>&1 || { cat "$SCRATCH/configure.log"; exit 1; }
fi
status=0
targets="--target forge --target forge_nnue_pawn_pair_tests"
run_tests() { (cd "$SCRATCH" && "$BUILD/forge_nnue_pawn_pair_tests" "$BUILD/forge" 3000 2>&1); }
# shellcheck disable=SC2086
cmake --build "$BUILD" $targets -j "${JOBS:-1}" > "$SCRATCH/build_clean.log" 2>&1 || { tail -20 "$SCRATCH/build_clean.log"; exit 1; }
echo "unmutated: $(run_tests | tail -1)"
mutate() { # name file old new
  local name=$1 file=$2 old=$3 new=$4
  if [ "${#selected[@]}" -gt 0 ] && [[ ! " ${selected[*]} " == *" $name "* ]]; then return; fi
  cp "$ROOT/$file" "$SRC/$file"
  python3 - "$SRC/$file" "$old" "$new" <<'PY' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if s.count(old) != 1: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
  # shellcheck disable=SC2086
  if ! cmake --build "$BUILD" $targets -j "${JOBS:-1}" > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    out=$(run_tests)
    fails=$(printf '%s\n' "$out" | grep -c '^FAIL' || true)
    first=$(printf '%s\n' "$out" | grep -m1 '^FAIL' | cut -c1-200 || true)
    if [ "$fails" -gt 0 ]; then echo "MUTATION $name -> caught: $fails failing checks ($(printf '%s\n' "$out" | tail -1)); first: $first"
    else echo "MUTATION $name -> NOT caught ($(printf '%s\n' "$out" | tail -1))"; status=1; fi
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
selected=("$@")
H=include/forge/nnue_v2.hpp
E=src/search/evaluation_extra.inc
V=src/search/evaluation_v2.inc
mutate offset_file_guard_wrong $H '{7, ~FileABB}, {8, ~0ULL}' '{7, ~FileHBB}, {8, ~0ULL}'
mutate black_not_rank_flipped $H 'if (perspective == Black) bb = __builtin_bswap64(bb);' '(void)perspective;'
mutate colour_pair_swapped $H '((c1 * 2 + c2) * PawnPairOffsets + o) * 64' '((c2 * 2 + c1) * PawnPairOffsets + o) * 64'
mutate pawn_moves_not_detected $E 'const bool pawn_move = pawns && nnue::v2::touches_pawns(dirty);' 'const bool pawn_move = false;'
mutate list_not_tracked_after_refresh $E 'child->accumulator.values[c].data(), pawns ? &pawn_lists[c] : nullptr);' 'child->accumulator.values[c].data(), nullptr);'
mutate loader_skips_pawn_block src/nnue.cpp 'for (std::size_t i = 0; i < wp_count; ++i, offset += 2) net->wp.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;' 'offset += 2 * wp_count;'
mutate selection_ignores_pawn_bit $V 'if (net != nullptr && (net->threats != threats || net->pawn_pairs != pawns)) {' 'if (net != nullptr && net->threats != threats) {'
# leave the copy unmutated and built
# shellcheck disable=SC2086
cmake --build "$BUILD" $targets -j "${JOBS:-1}" > "$SCRATCH/build_restore.log" 2>&1
echo "mutation_check status=$status"
exit $status
