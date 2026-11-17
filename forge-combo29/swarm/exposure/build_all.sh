#!/usr/bin/env bash
# Rebuild the three arms of the exposure audit and rerun every measurement.
#
# THE THREE ARMS
#   base     -- the engine at commit 6b98f217, unmodified.
#   patched  -- base + seat 12 (swarm/12/job1/two_doors_mate.patch.txt) + seat 27
#               (swarm/27/job1/drawn_root_reporting.patch.txt). The repair the owner is
#               asked to ship. Must compose to src/search.cpp sha256 24912a43...
#   nobail   -- INSTRUMENT ONLY, never a shipping candidate: the bail's guard is
#               compiled out so a drawn root can be searched. Without it, "the move the
#               search would have played" is unmeasurable, because the base searches
#               nothing on these positions.
#
# BUILD TRAP (this machine): /usr/bin/c++ is clang 18 with a broken header path. Build
# with g++ and the gcc-13 library path, or the build fails in ways that look like source
# errors.
set -euo pipefail

REPO_ROOT=${REPO_ROOT:-$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null || true)}
if [ -z "$REPO_ROOT" ]; then
  echo "FATAL: could not find the repository root; set REPO_ROOT explicitly" >&2
  exit 1
fi
WORK=${WORK:-/tmp/forge-exposure}
BASE_COMMIT=${BASE_COMMIT:-6b98f217}
BUILD_DIR="$WORK/build"

echo "repo:    $REPO_ROOT"
echo "work:    $WORK"
echo "commit:  $BASE_COMMIT"

mkdir -p "$WORK"
cd "$REPO_ROOT"

# ---------------------------------------------------------------- sources
if [ ! -d "$WORK/base" ]; then
  git worktree prune
  git worktree add --detach -f "$WORK/base" "$BASE_COMMIT"
fi
rm -rf "$WORK/patched" "$WORK/nobail"
cp -a "$WORK/base" "$WORK/patched"

# ---------------------------------------------------------------- patches
# The -p level differs per patch and this is the documented trap: seat 12's hunks name
# a/forge-combo29/src/... so it is -p1 from the REPO ROOT; seat 27's name a/src/... so
# it is -p1 from INSIDE forge-combo29/. Using one level for both silently skips a hunk,
# so every exit code is checked.
git show origin/for-fable-and-opus/swarm-12:forge-combo29/swarm/12/job1/two_doors_mate.patch.txt \
  > "$WORK/two_doors.patch"
git show origin/for-fable-and-opus/swarm-27:forge-combo29/swarm/27/job1/drawn_root_reporting.patch.txt \
  > "$WORK/reporting.patch"

cd "$WORK/patched"
patch -p1 < "$WORK/two_doors.patch"
cd "$WORK/patched/forge-combo29"
patch -p1 < "$WORK/reporting.patch"

GOT=$(sha256sum "$WORK/patched/forge-combo29/src/search.cpp" | cut -d' ' -f1)
WANT=24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671
echo "composed src/search.cpp sha256: $GOT"
if [ "$GOT" != "$WANT" ]; then
  echo "FATAL: composed repair does not match the expected sha256" >&2
  exit 1
fi

# ---------------------------------------------------------------- nobail instrument
# The instrument starts from the PATCHED tree and then removes the guard, so that the
# only difference between `patched` and `nobail` is whether a drawn root is searched.
# (Deriving it from the base tree instead fails loudly: the `root_draw_adjudicated`
# variable does not exist there, which is how this was caught.)
rm -rf "$WORK/nobail"
cp -a "$WORK/patched" "$WORK/nobail"
python3 - "$WORK/nobail/forge-combo29/src/search.cpp" <<'PY'
import sys
path = sys.argv[1]
src = open(path).read()
old = """    bool root_draw_adjudicated = !legal.empty() && (board.is_repetition() ||
                                                    board.halfmove_clock() >= 100 ||
                                                    board.is_insufficient_material());"""
new = """    // INSTRUMENT BUILD ONLY: the bail is disarmed so the same position can be
    // searched normally. NOT a shipped configuration.
    bool root_draw_adjudicated = false;"""
if src.count(old) != 1:
    raise SystemExit(f"FATAL: expected exactly one match, found {src.count(old)}")
open(path, "w").write(src.replace(old, new))
print("nobail instrument applied")
PY

# ---------------------------------------------------------------- build all three
for arm in base patched nobail; do
  src="$WORK/$arm/forge-combo29"
  mkdir -p "$BUILD_DIR/$arm"
  (
    cd "$BUILD_DIR/$arm"
    LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
      cmake "$src" -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release >/dev/null
    LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j"$(nproc)" 2>&1 | tail -2
  )
done

echo
echo "binaries:"
sha256sum "$BUILD_DIR"/*/forge
