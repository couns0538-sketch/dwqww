#!/usr/bin/env bash
# Build every variant this audit compares, from a clean tree at the base commit.
#
# The two traps this script exists to avoid:
#   - /usr/bin/c++ is clang 18 with a broken header path. /usr/bin/g++ is the
#     compiler that works, and it needs LIBRARY_PATH for the gcc-13 runtime.
#   - A lower-march build with FORGE_PORTABLE=OFF does NOT compile. That is a
#     result, not a failure to work around: the script records the error and
#     keeps going so the evidence file shows what happened.
set -uo pipefail

SRC="${SRC:-/tmp/wt/base/forge-combo29}"
OUT="${OUT:-/tmp/build}"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

build() {
  local name="$1" march="$2" portable="$3"
  local dir="$OUT/$name"
  rm -rf "$dir"
  echo "=== $name: -march=$march FORGE_PORTABLE=$portable ==="
  if ! cmake -S "$SRC" -B "$dir" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
        -DFORGE_MARCH="$march" \
        -DFORGE_PORTABLE="$portable" > "$OUT/$name.configure.log" 2>&1; then
    echo "  CONFIGURE FAILED (see $name.configure.log)"
    return 1
  fi
  if ! cmake --build "$dir" -j4 > "$OUT/$name.build.log" 2>&1; then
    echo "  BUILD FAILED -- this is the recorded result, not a script error:"
    grep -E '#error|Error [0-9]' "$OUT/$name.build.log" | head -4
    return 2
  fi
  echo "  ok: $(ls -l "$dir/forge" | awk '{print $5}') bytes"
  return 0
}

build native native  OFF
build v2     x86-64-v2 ON
build v3     x86-64-v3 ON
build v4both x86-64-v4 OFF

# Controls: the same lower ISA with the switches left ON. Expected to fail to
# compile, and the #error is what makes the failure legible instead of a
# miscompile on a CPU that lacks the instruction.
build v2-switchon x86-64-v2 OFF
build v3-switchon x86-64-v3 OFF
