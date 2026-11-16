#!/usr/bin/env bash
# verify_patch_order.sh <base-commit> <seat12-patch> <seat27-patch>
# Proves, from a clean tree, that the two patches compose in EITHER ORDER to a byte-identical
# src/search.cpp, and that the only real constraint is each patch's -p level.
#
# Written after seat 12 corrected my claim that "the reverse order fails". It does not: my failure
# came from running their patch at the wrong -p level. This script measures all of it instead of
# asserting it, and prints every exit code.
#
# Usage (from anywhere):
#   bash verify_patch_order.sh 6b98f217 \
#        /path/to/s12/two_doors_mate.patch.txt \
#        /path/to/27/job1/drawn_root_reporting.patch.txt
#
# Self-tests it was checked against (all four were run, exit codes read WITHOUT a pipe, because
# `| tail` masks $? -- a trap I fell into while testing this very script):
#   1. both patches present, correct paths          -> PASS, exit 0
#   2. a patch file that does not exist             -> "FAIL: cannot read patch file", exit 2
#   3. a patch that applies to nothing              -> "FAIL: at least one patch did not apply", exit 1
#   4. relative paths from the caller's directory   -> resolved to absolute first, so 1 applies
# The first version kept the paths relative and did not check patch's exit code, so it printed PASS
# while seat 12's patch had silently skipped. The absolute-path resolution and the exit-code gate
# above exist because of that; do not remove them.
set -u
BASE="${1:?base commit}"
# Resolve every path to ABSOLUTE before any cd. The first version kept them relative, so after `cd` into a
# temp archive the patch files "did not exist", patch failed, and the script STILL printed PASS because it
# never checked the exit codes -- the very mistake it exists to warn about. Caught by re-reading the output.
S12=$(readlink -f "${2:?seat 12 patch}")
S27=$(readlink -f "${3:?seat 27 patch}")
SRC=$(readlink -f "${4:-/agent/repos/base}")   # a git repo that has BASE
for f in "$S12" "$S27"; do
  [ -r "$f" ] || { echo "FAIL: cannot read patch file $f"; exit 2; }
done

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fresh() { # fresh <dir>
  mkdir -p "$1"
  git -C "$SRC" archive "$BASE" forge-combo29/src | tar -x -C "$1"
}

echo "== base $BASE"
echo "== seat 12 patch: $S12"
echo "== seat 27 patch: $S27"
echo

echo "-- hunk headers (this is why the -p levels differ) --"
echo "   seat 12: $(head -1 "$S12")"
echo "   seat 27: $(head -1 "$S27")"
echo

# --- ORDER A: seat 12 first (repo root, -p1), then seat 27 (inside forge-combo29, -p1)
fresh "$TMP/a"
cd "$TMP/a"; patch -p1 < "$S12" > /dev/null 2>&1; RC12A=$?; echo "ORDER A  seat12 -p1 from root      rc=$RC12A"
cd "$TMP/a/forge-combo29"; patch -p1 < "$S27" > /dev/null 2>&1; RC27A=$?; echo "ORDER A  seat27 -p1 from inside    rc=$RC27A"
SHA_A=$(sha256sum "$TMP/a/forge-combo29/src/search.cpp" | awk '{print $1}')
echo "ORDER A  src/search.cpp $SHA_A"
echo

# --- ORDER B: seat 27 first (inside forge-combo29, -p1), then seat 12 (repo root, -p1)
fresh "$TMP/b"
cd "$TMP/b/forge-combo29"; patch -p1 < "$S27" > /dev/null 2>&1; RC27B=$?; echo "ORDER B  seat27 -p1 from inside    rc=$RC27B"
cd "$TMP/b"; patch -p1 < "$S12" > /dev/null 2>&1; RC12B=$?; echo "ORDER B  seat12 -p1 from root      rc=$RC12B"
SHA_B=$(sha256sum "$TMP/b/forge-combo29/src/search.cpp" | awk '{print $1}')
echo "ORDER B  src/search.cpp $SHA_B"
echo

# --- the trap: one flag for both, from inside forge-combo29
fresh "$TMP/c"
cd "$TMP/c/forge-combo29"
patch -p1 < "$S12" > /dev/null 2>&1; RC=$(($?))
echo "TRAP     seat12 -p1 from INSIDE forge-combo29 rc=$RC   (nonzero = this is what misled me)"
patch -p2 < "$S12" > /dev/null 2>&1; echo "TRAP     seat12 -p2 from INSIDE forge-combo29 rc=$?   (zero = the correct level here)"
echo

echo "== verdict"
if [ "$RC12A" -ne 0 ] || [ "$RC27A" -ne 0 ] || [ "$RC12B" -ne 0 ] || [ "$RC27B" -ne 0 ]; then
  echo "FAIL: at least one patch did not apply (rc: 12A=$RC12A 27A=$RC27A 27B=$RC27B 12B=$RC12B)."
  echo "      A byte-identical pair is meaningless if a patch silently skipped -- check the -p levels."
  exit 1
fi
if [ "$SHA_A" = "$SHA_B" ]; then
  echo "PASS: both orders give a byte-identical src/search.cpp ($SHA_A). Order does not matter."
  echo "      The -p level differs per patch: seat 12 = -p1 from the repo root or -p2 from inside"
  echo "      forge-combo29; seat 27 = -p1 from inside forge-combo29."
  exit 0
fi
echo "FAIL: the two orders produced different files:"
echo "  A $SHA_A"
echo "  B $SHA_B"
exit 1
