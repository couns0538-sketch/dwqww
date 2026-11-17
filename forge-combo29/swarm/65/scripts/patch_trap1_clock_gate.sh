#!/usr/bin/env bash
# Patch trap 1 and measure it: the clock gate must not depend on which clock the
# caller happened to send.
#
# The defect: `parse_limits` stores a clock in `limits.time_ms` only when it is the
# *side to move's* clock (src/uci.cpp:121-122). A harness that sends only the
# opponent's clock therefore looks like "no clock at all" to the engine, with two
# consequences:
#
#   1. the book gate (`limits.time_ms >= 0`) does not fire, so a position with a
#      book entry is searched instead of booked;
#   2. worse, the search is not time-limited at all. It runs until `stop`.
#
# The fix records each side's clock under its own name and resolves the budget at
# the end of the command: the mover's clock if it was given, otherwise the
# opponent's. Existing callers are unaffected, because a caller that sends the
# mover's clock takes the first branch exactly as before.
#
# This is a UCI-layer change and nothing in search.cpp moves, but unlike the trap-2
# patch the pins are NOT automatically safe here: `limits.time_ms` feeds the time
# manager, so a mistake could change a timed search. The 11 documented pins are
# checked on both builds.
#
# Usage: bash swarm/65/scripts/patch_trap1_clock_gate.sh [repo_root] [commit]

set -u -o pipefail

REPO="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
COMMIT="${2:-6b98f217}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EV="$HERE/../evidence"
SHORT=$(echo "$COMMIT" | cut -c1-8)
WT="${WT:-/tmp/sw65-trap1-wt-$SHORT}"
B_LOCK="${B_LOCK:-/tmp/sw65-trap1-lock-$SHORT}"
B_FIX="${B_FIX:-/tmp/sw65-trap1-fix-$SHORT}"
PATCH="$HERE/../patches/trap1-clock-gate-both-clocks.patch"

mkdir -p "$EV" "$(dirname "$PATCH")"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

echo "== 0. worktree at $COMMIT =="
cd "$REPO" || exit 1
git worktree remove --force "$WT" 2>/dev/null || rm -rf "$WT"
git worktree add --detach "$WT" "$COMMIT" > "$EV/trap1-worktree.log" 2>&1 || {
  echo "worktree failed"; exit 1; }
SRC="$WT/forge-combo29"
echo "   source $SRC"

build() {
  cmake -S "$1" -B "$2" -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=native \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ > "$EV/trap1-build.log" 2>&1 &&
  cmake --build "$2" -j"$(nproc)" >> "$EV/trap1-build.log" 2>&1
}

echo
echo "== 1. unpatched binary, full documented pin set =="
rm -rf "$B_LOCK"
build "$SRC" "$B_LOCK" || { echo "unpatched build failed"; exit 1; }
python3 "$HERE/q13_pins.py" "$B_LOCK/forge" | tee "$EV/trap1-pins-lock.txt" || {
  echo "the UNPATCHED build does not match the documented pins; stopping"; exit 1; }

echo
echo "== 2. apply the patch =="
python3 - "$SRC/src/uci.cpp" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text()

# (a) record each side's clock under its own name instead of only the mover's.
old_clocks = """        else if (token == "wtime") { const std::int64_t value = read_clock(); if (side == forge::White) limits.time_ms = value; }
        else if (token == "btime") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.time_ms = value; }
        else if (token == "winc") { const std::int64_t value = read_clock(); if (side == forge::White) limits.increment_ms = value; }
        else if (token == "binc") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.increment_ms = value; }"""
new_clocks = """        else if (token == "wtime") { wtime_ms = read_clock(); }
        else if (token == "btime") { btime_ms = read_clock(); }
        else if (token == "winc") { winc_ms = read_clock(); }
        else if (token == "binc") { binc_ms = read_clock(); }"""
assert old_clocks in s, "clock parse block not found; the base changed"
assert s.count(old_clocks) == 1
s = s.replace(old_clocks, new_clocks)

# (b) declare the four accumulators.
old_decl = """    const forge::Color side = board.side_to_move();
    for (std::size_t i = 0; i < tokens.size();) {"""
new_decl = """    const forge::Color side = board.side_to_move();
    std::int64_t wtime_ms = -1;
    std::int64_t btime_ms = -1;
    std::int64_t winc_ms = 0;
    std::int64_t binc_ms = 0;
    for (std::size_t i = 0; i < tokens.size();) {"""
assert s.count(old_decl) == 1
s = s.replace(old_decl, new_decl)

# (c) resolve the budget at the end of parse_limits.
old_ret = """    return limits;
}"""
new_ret = """    // A clock belongs to a side, but a search only needs a budget. Use the mover's
    // clock when it was given and fall back to the opponent's otherwise: a caller
    // that sends only one clock is still describing a timed game, and reading that
    // as "no clock" leaves the search unbounded.
    const std::int64_t own_time = (side == forge::White) ? wtime_ms : btime_ms;
    const std::int64_t other_time = (side == forge::White) ? btime_ms : wtime_ms;
    const std::int64_t own_inc = (side == forge::White) ? winc_ms : binc_ms;
    const std::int64_t other_inc = (side == forge::White) ? binc_ms : winc_ms;
    if (own_time >= 0) {
        limits.time_ms = own_time;
        limits.increment_ms = own_inc;
    } else if (other_time >= 0) {
        limits.time_ms = other_time;
        limits.increment_ms = other_inc;
    }
    return limits;
}"""
assert s.count(old_ret) == 1, "return site is not unique"
s = s.replace(old_ret, new_ret)

p.write_text(s)
print("   patched: both clocks recorded, mover's preferred, opponent's as fallback")
PY

# (d) fail if the clock variables are now unused anywhere they should not be.
if grep -q "side == forge::White) limits.time_ms" "$SRC/src/uci.cpp"; then
  echo "patch incomplete: the old side-conditional assignments are still present"; exit 1
fi

echo
echo "== 3. patched binary, pins must be identical =="
rm -rf "$B_FIX"
build "$SRC" "$B_FIX" || { echo "patched build failed"; sed -n '1,60p' "$EV/trap1-build.log"; exit 1; }
python3 "$HERE/q13_pins.py" "$B_FIX/forge" | tee "$EV/trap1-pins-fix.txt" || {
  echo "PATCH CHANGED THE PINS"; exit 1; }
if ! diff <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap1-pins-lock.txt" | grep -v '^binary ') \
            <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap1-pins-fix.txt" | grep -v '^binary ') >/dev/null; then
  echo "PIN OUTPUT DIFFERS between lock and patched builds:"
  diff <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap1-pins-lock.txt" | grep -v '^binary ') \
       <(sed 's/ time [0-9]*//; s/ nps [0-9]*//' "$EV/trap1-pins-fix.txt" | grep -v '^binary ')
  exit 1
fi
echo "   pins identical — patch does not change node counts"

# Save the diff for review.
( cd "$WT" && git diff > "$PATCH" )
echo "   patch saved to $PATCH"

echo
echo "== 4. trap 1 before and after, including the unbounded-search case =="
python3 "$HERE/q16_trap1_patch_effect.py" "$B_LOCK/forge" "$B_FIX/forge" \
  | tee "$EV/trap1-effect.txt" || { echo "TRAP-1 CHECK FAILED"; exit 1; }

echo
echo "== 5. trap 2 and trap 3 must be unaffected =="
python3 "$HERE/q17_traps_2_3_after_trap1.py" "$B_FIX/forge" | tee "$EV/trap1-trap2-3.txt" || {
  echo "TRAP 2/3 CHECK FAILED"; exit 1; }

echo
echo "done. evidence: $EV/trap1-*"
