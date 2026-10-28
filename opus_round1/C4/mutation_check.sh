#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that forge_nnue_v2_tests fails.
# usage: opus_round1/C4/mutation_check.sh <scratch_dir>   (run from the repository root; needs cmake, ninja, g++)
# Environment: CXX (compiler), MUTATION_LINK_FLAGS (e.g. -static on MinGW), JOBS (default 1).
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
mkdir -p "$SRC"
cp -a "$ROOT/." "$SRC/"
cmake -S "$SRC" -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=${CXX:-g++}" \
  "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
  ${MUTATION_LINK_FLAGS:+"-DCMAKE_EXE_LINKER_FLAGS=$MUTATION_LINK_FLAGS"} > "$SCRATCH/configure.log" 2>&1 || { cat "$SCRATCH/configure.log"; exit 1; }
status=0
target=forge_nnue_v2_tests
cmake --build "$BUILD" --target "$target" -j "${JOBS:-1}" > "$SCRATCH/build_clean.log" 2>&1 || { tail -20 "$SCRATCH/build_clean.log"; exit 1; }
clean=$("$BUILD/$target" 4000 2>&1 | tail -1)
echo "unmutated: $clean"
mutate() { # name file old new
  local name=$1 file=$2 old=$3 new=$4
  cp "$ROOT/$file" "$SRC/$file"
  python3 - "$SRC/$file" "$old" "$new" <<'PY' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if s.count(old) != 1: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
  if ! cmake --build "$BUILD" --target "$target" -j "${JOBS:-1}" > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    # 4000 plies per walk net keeps each run short; the failing checks are listed.
    out=$("$BUILD/$target" 4000 2>&1)
    last=$(printf '%s\n' "$out" | tail -1)
    fails=$(printf '%s\n' "$out" | grep -c '^FAIL' || true)
    first=$(printf '%s\n' "$out" | grep -m1 '^FAIL' || true)
    if [ "$fails" -gt 0 ]; then echo "MUTATION $name -> caught: $fails failing checks ($last); first: $first"
    else echo "MUTATION $name -> NOT caught ($last)"; status=1; fi
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
H=include/forge/nnue_v2.hpp
E=src/search/evaluation_v2.inc
mutate flip_from_file_d $H 'net.mirror && (relative & 7) >= 4 ? 7 : 0' 'net.mirror && (relative & 7) >= 3 ? 7 : 0'
mutate king_no_rank_flip $H 'const int relative = perspective == White ? king_square : king_square ^ 56;' 'const int relative = king_square;'
mutate feature_flip_6 $H '(perspective == White ? square : square ^ 56) ^ key.flip;' '(perspective == White ? square : square ^ 56) ^ (key.flip ? 6 : 0);'
mutate cache_pieces_stale $H '        entry.pieces[static_cast<std::size_t>(code)] = now;' '        (void)now;'
mutate undo_swapped $H 'if (change.add) bb &= ~square_bb(change.square);' 'if (!change.add) bb &= ~square_bb(change.square);'
mutate no_key_change_refresh $E 'if (!(moved == key[c])) [[unlikely]] {' 'if (false) {'
mutate ancestor_king_ignored $E 'king[static_cast<std::size_t>(color_of(dirty.changes[0].piece))] = dirty.changes[0].square;' '(void)dirty;'
mutate refresh_wrong_ply $E 'for (int k = 0; k < i; ++k) nnue::v2::undo(pieces, (ss - k)->dirty);' 'for (int k = 0; k + 1 < i; ++k) nnue::v2::undo(pieces, (ss - k)->dirty);'
mutate loader_no_checksum src/nnue.cpp 'if (stored != checksum) return fail(error, "checksum mismatch (file damaged)");' '(void)stored;'
mutate loader_map_unchecked src/nnue.cpp 'if (bytes[52 + i] >= king_buckets) return fail(error, "king bucket map entry out of range");' '(void)i;'
echo "mutation_check status=$status"
exit $status
