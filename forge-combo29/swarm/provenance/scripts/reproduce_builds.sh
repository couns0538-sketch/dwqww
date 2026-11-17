#!/bin/sh
# Reproduce the two binaries the swarm seats cited, from committed text only.
#
# The question this answers is not "does the sha256 look plausible" but "can a
# third party, with nothing but this repository, arrive at that byte string". If
# the answer is yes, the hash is a BUILD, and every row that names it is
# re-derivable. If no, it is a claim.
#
# Both builds are from commit 6b98f217 (the audit base), which IS reachable from
# refs (checked with git rev-list --all, see evidence/refs_census.txt).
#
# Usage:  sh scripts/reproduce_builds.sh [workdir]
set -u
REPO=${REPO:-/agent/repos/dwqww}
BASE=${BASE:-6b98f2170a3210e71beed04bbd2553972c253ed7}
WORK=${1:-/tmp/prov-repro}
mkdir -p "$WORK"

# Toolchain pin. /usr/bin/c++ on this image is clang 18 with a broken header path;
# g++ 13 is the compiler the seats recorded, so the reproduction names it explicitly.
CXX=/usr/bin/g++
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
export LIBRARY_PATH

echo "=== refs census (the command that ENUMERATES; a negative claim needs one) ==="
git -C "$REPO" rev-list --all --count
git -C "$REPO" for-each-ref --format='%(refname)' | wc -l

echo
echo "=== base build: $BASE as committed ==="
rm -rf "$WORK/base" && mkdir -p "$WORK/base"
git -C "$REPO" archive "$BASE" forge-combo29 | tar x -C "$WORK/base"
cmake -S "$WORK/base/forge-combo29" -B "$WORK/base/build" \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" >"$WORK/base/cmake.log" 2>&1
cmake --build "$WORK/base/build" -j8 >>"$WORK/base/cmake.log" 2>&1
BASE_SHA=$(sha256sum "$WORK/base/build/forge" | cut -d' ' -f1)
echo "base binary sha256 : $BASE_SHA"
echo "seat-reported      : e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83"
[ "$BASE_SHA" = "e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83" ] \
  && echo "verdict            : REPRODUCED byte-exact" \
  || echo "verdict            : DIFFERS"

echo
echo "=== PC r15 build: FABLE_TO_swarm_5.md patch applied to the same base ==="
# The patch text lives INSIDE the committed markdown, between the fence at line 55
# and the final fence. So it is committed as text and its sha256 can be checked
# before it is applied -- which is what the handoff document itself asks for.
git -C "$REPO" cat-file -p 12772bb790459856ed42d512a28721b8f96c4249 > "$WORK/F5.md"
awk 'NR>55 && /^```$/{exit} NR>55' "$WORK/F5.md" > "$WORK/pc_r15.patch"
PATCH_SHA=$(sha256sum "$WORK/pc_r15.patch" | cut -d' ' -f1)
echo "patch sha256       : $PATCH_SHA"
echo "documented prefix  : d6bd72c531f785f4"
case "$PATCH_SHA" in
  d6bd72c531f785f4*) echo "verdict            : patch text VERIFIES against its recorded sha256" ;;
  *)                 echo "verdict            : PATCH TEXT DOES NOT MATCH -- stop, do not build" ;;
esac

rm -rf "$WORK/r15" && mkdir -p "$WORK/r15"
git -C "$REPO" archive "$BASE" forge-combo29 | tar x -C "$WORK/r15"
( cd "$WORK/r15/forge-combo29" && patch -p1 <"$WORK/pc_r15.patch" ) >"$WORK/r15/patch.log" 2>&1
echo "patch exit         : $?"
cmake -S "$WORK/r15/forge-combo29" -B "$WORK/r15/build" \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
      -DCMAKE_CXX_FLAGS="-DFORGE_MATE_ALPHA_GUARD=1" >"$WORK/r15/cmake.log" 2>&1
cmake --build "$WORK/r15/build" -j8 >>"$WORK/r15/cmake.log" 2>&1
R15_SHA=$(sha256sum "$WORK/r15/build/forge" | cut -d' ' -f1)
echo "r15 binary sha256  : $R15_SHA"
echo "seat-reported      : 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4"
[ "$R15_SHA" = "068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4" ] \
  && echo "verdict            : REPRODUCED byte-exact" \
  || echo "verdict            : DIFFERS"

echo
echo "=== pins, sent over stdin as UCI commands (not as argv) ==="
echo "NOTE: ./forge bench 11 as an argv prints nothing and exits 0 -- bench N is a"
echo "      UCI command, so every bench below is fed on stdin."
for b in 11 13 16; do
  printf 'bench %s\nquit\n' "$b" | "$WORK/base/build/forge" 2>&1 | grep 'bench depth' | tail -1 | sed "s/^/  base  /"
  printf 'bench %s\nquit\n' "$b" | "$WORK/r15/build/forge"  2>&1 | grep 'bench depth' | tail -1 | sed "s/^/  r15   /"
done
echo "  documented on the PC's build: 312866 / 862329 / 3024920"
