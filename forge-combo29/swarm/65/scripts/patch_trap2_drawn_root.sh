#!/usr/bin/env bash
# Patch trap 2 and measure it: the book must not pre-empt drawn-root detection.
#
# The defect: `src/uci.cpp` consults the opening book before the search is
# entered. `src/search.cpp` has a drawn-root bail that reports `score cp 0` with an
# empty pv for a repetition, a fifty-move root, or insufficient material. The book
# answers first, so on positions with a book entry that signal never appears.
#
# The fix is ordering, expressed as a predicate: refuse to book when the root is
# one the search would have bailed on. Nothing in search.cpp changes, so bench and
# perft must be bit-identical — which this script verifies rather than asserts.
#
# Usage: bash swarm/65/scripts/patch_trap2_drawn_root.sh [repo_root] [commit]
#
# Steps:
#   1. clean worktree at the base commit
#   2. build the unpatched binary, verify the full documented pin set
#   3. apply the one-hunk patch, rebuild, verify the same pins are unchanged
#   4. re-measure the three trap behaviours on the patched build
#   5. re-measure the drawn-condition matrix: 2/2 pre-empted must become 0/2,
#      and the 4 non-entry roots must stay correct
#   6. confirm the book still fires on ordinary book positions (the fix must not
#      disable the book)

set -u -o pipefail

REPO="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
COMMIT="${2:-6b98f217}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EV="$HERE/../evidence"
SHORT=$(echo "$COMMIT" | cut -c1-8)
WT="${WT:-/tmp/sw65-trap2-wt-$SHORT}"
B_LOCK="${B_LOCK:-/tmp/sw65-trap2-lock-$SHORT}"
B_FIX="${B_FIX:-/tmp/sw65-trap2-fix-$SHORT}"

mkdir -p "$EV"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

echo "== 0. worktree at $COMMIT =="
cd "$REPO" || exit 1
git worktree remove --force "$WT" 2>/dev/null || rm -rf "$WT"
git worktree add --detach "$WT" "$COMMIT" > "$EV/trap2-worktree.log" 2>&1 || {
  echo "worktree failed"; exit 1; }
SRC="$WT/forge-combo29"
echo "   source $SRC"

build() {  # build <srcdir> <builddir>
  cmake -S "$1" -B "$2" -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ > "$EV/trap2-build.log" 2>&1 &&
  cmake --build "$2" -j"$(nproc)" >> "$EV/trap2-build.log" 2>&1
}

echo
echo "== 1. build the unpatched binary and verify the documented pins =="
rm -rf "$B_LOCK"
build "$SRC" "$B_LOCK" || { echo "unpatched build failed"; exit 1; }
python3 "$HERE/q13_pins.py" "$B_LOCK/forge" | tee "$EV/trap2-pins-lock.txt" || {
  echo "the UNPATCHED build does not match the documented pins; stopping rather than"; \
  echo "patching on top of a build that cannot be trusted"; exit 1; }

echo
echo "== 2. apply the patch =="
python3 - "$SRC/src/uci.cpp" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text()

old = """                if (game_search && own_book && !book.empty() && game_ply(board) < book_depth) {"""
new = """                // A drawn root is reported by the search without searching (cp 0,
                // empty pv). That report is the caller's only in-band signal that the
                // position is drawn, so the book must not answer it first.
                const bool root_drawn = board.is_repetition() || board.halfmove_clock() >= 100 ||
                                        board.is_insufficient_material();
                if (game_search && own_book && !book.empty() && !root_drawn &&
                    game_ply(board) < book_depth) {"""
assert old in s, "gate line not found; the base changed"
assert s.count(old) == 1, "gate line is not unique"
p.write_text(s.replace(old, new))
print("   patched: book gate now refuses a drawn root")
PY

echo
echo "== 3. build the patched binary and verify the pins are unchanged =="
rm -rf "$B_FIX"
build "$SRC" "$B_FIX" || { echo "patched build failed"; exit 1; }
python3 "$HERE/q13_pins.py" "$B_FIX/forge" | tee "$EV/trap2-pins-fix.txt" || {
  echo "PATCH CHANGED THE PINS — the patch is not search-neutral"; exit 1; }
if ! diff <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap2-pins-lock.txt" | grep -v '^binary ') \
            <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap2-pins-fix.txt" | grep -v '^binary ') > /dev/null; then
  echo "PIN OUTPUT DIFFERS between lock and patched builds (beyond time/nps):"
  diff <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap2-pins-lock.txt" | grep -v '^binary ') \
       <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap2-pins-fix.txt" | grep -v '^binary ')
  exit 1
fi
echo "   pins identical to the unpatched build (time/nps removed) — patch is search-neutral"

echo
echo "== 4. trap 2, before and after =="
python3 "$HERE/q14_trap2_patch_effect.py" "$B_LOCK/forge" "$B_FIX/forge" \
  | tee "$EV/trap2-effect.txt" || { echo "TRAP-2 CHECK FAILED"; exit 1; }

echo
echo "== 5. traps 1 and 3 must be unchanged by the patch =="
python3 "$HERE/q15_traps_unchanged.py" "$B_FIX/forge" | tee "$EV/trap2-trap1-3.txt" || {
  echo "TRAP 1/3 CHECK FAILED"; exit 1; }

echo
echo "done. evidence: $EV/trap2-*"
echo "patched source kept at $SRC for inspection"
