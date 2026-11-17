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

WORK="${PORTABLE_WORK:-/tmp/build}"
SRC="${SRC:-/tmp/wt/base/forge-combo29}"
OUT="${OUT:-$WORK}"
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13

if [[ ! -f "$SRC/CMakeLists.txt" ]]; then
  printf 'build_all.sh: no CMakeLists.txt at %s\n' "$SRC" >&2
  printf '  set SRC to a forge-combo29 checkout (e.g. from git worktree add)\n' >&2
  exit 2
fi
if [[ ! -d "$OUT" ]]; then
  printf 'build_all.sh: output dir %s does not exist\n' "$OUT" >&2
  exit 2
fi

build() {
  local name="$1" march="$2" portable="$3"
  local dir="$OUT/$name"
  echo "=== $name: -march=$march FORGE_PORTABLE=$portable ==="
  # Only ever remove a directory this script created: the marker below is written
  # into every build dir it makes, so a mistyped OUT cannot delete anything else.
  if [[ -d "$dir" && ! -f "$dir/.portable-build-dir" ]]; then
    printf '  refusing to replace %s: not a directory this script created\n' "$dir" >&2
    return 1
  fi
  rm -rf "$dir"
  mkdir -p "$dir"
  : > "$dir/.portable-build-dir"
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
