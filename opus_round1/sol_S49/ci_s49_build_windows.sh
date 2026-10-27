#!/usr/bin/env bash
# S49 Windows box run, build step (MSYS2 UCRT64 g++ on a GitHub-hosted Windows runner): the lock tree and a TEST-ONLY
# copy with test_only_synthetic_slowdown.patch (-DFORGE_S49_SYNTHETIC_SLOWDOWN_PCT=5), both statically linked so
# pwsh can start them outside MSYS2. Used by .github/workflows/opus-sol-s49-box-windows.yml.
# usage: opus_round1/sol_S49/ci_s49_build_windows.sh <out_dir>
set -euo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
J="$ROOT/opus_round1/sol_S49"
FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
g++ --version | head -1 | tee "$OUT/toolchain_windows.log"
cmake -S "$ROOT" -B "$OUT/build_lock" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=$FLAGS" \
  -DCMAKE_EXE_LINKER_FLAGS=-static > "$OUT/configure_lock.log" 2>&1 || { tail -40 "$OUT/configure_lock.log"; exit 1; }
cmake --build "$OUT/build_lock" --target forge -j"$(nproc)" > "$OUT/build_lock.log" 2>&1 || { tail -40 "$OUT/build_lock.log"; exit 1; }
SLOW_SRC="$OUT/src_slow"
mkdir -p "$SLOW_SRC"
(cd "$ROOT" && tar -cf - src include tests bench tools CMakeLists.txt) | (cd "$SLOW_SRC" && tar -xf -)
(cd "$SLOW_SRC" && git apply --check -p1 "$J/test_only_synthetic_slowdown.patch" && git apply -p1 "$J/test_only_synthetic_slowdown.patch") \
  > "$OUT/patch_slow.log" 2>&1 || { cat "$OUT/patch_slow.log"; exit 1; }
cmake -S "$SLOW_SRC" -B "$OUT/build_slow" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  "-DCMAKE_CXX_FLAGS=$FLAGS -DFORGE_S49_SYNTHETIC_SLOWDOWN_PCT=5" -DCMAKE_EXE_LINKER_FLAGS=-static \
  > "$OUT/configure_slow.log" 2>&1 || { tail -40 "$OUT/configure_slow.log"; exit 1; }
cmake --build "$OUT/build_slow" --target forge -j"$(nproc)" > "$OUT/build_slow.log" 2>&1 || { tail -40 "$OUT/build_slow.log"; exit 1; }
sha256sum "$OUT/build_lock/forge.exe" "$OUT/build_slow/forge.exe" | tee "$OUT/exe_sha256_windows.log"
