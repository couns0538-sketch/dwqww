#!/usr/bin/env bash
# Prove the sanitizer is linked into the binary, and prove it is NOT in the
# baseline binary. A zero from an unproven sanitizer is not a zero.
set -euo pipefail
SAN=${1:-/tmp/forge/build-ubsan/forge}
BASE=${2:-/tmp/forge/build-base/forge}
echo "== undefined-behaviour handlers referenced (nm | grep -c __ubsan_)"
echo "sanitizer build : $(nm "$SAN"  | grep -c __ubsan_ || true)"
echo "baseline build  : $(nm "$BASE" | grep -c __ubsan_ || true)"
echo "== address handlers"
echo "sanitizer build : $(nm "$SAN"  | grep -c __asan_ || true)"
echo "baseline build  : $(nm "$BASE" | grep -c __asan_ || true)"
echo "== distinct ubsan handlers by name"
nm "$SAN" | grep __ubsan_ | awk '{print $NF}' | sort -u
