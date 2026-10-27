#!/usr/bin/env bash
# Linux evidence for an Opus job branch (used by .github/workflows/opus-ci.yml, also runnable on the box).
#   release : box recipe (g++-14, CMake Release, x86-64-v3, no FMA contraction) -> bench x5 + perft +
#             kiwipete (uci_check --full), FMA count, ctest with the known-failure check
#   asan    : -DFORGE_ENABLE_SANITIZERS=ON (ASan+UBSan), recover off, ctest + known-failure check
#   tsan    : -fsanitize=thread, ctest + known-failure check, then opus_round1/*/tsan_extra.sh if present
# usage: opus_round1/ci/run_ci.sh <release|asan|tsan> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CI="$ROOT/opus_round1/ci"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
BD="$OUT/build_$MODE"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
status=0
case "$MODE" in
  release)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    echo "== compiler: $($CXX --version | head -1)" | tee "$OUT/identity.log"
    echo "== forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)" | tee -a "$OUT/identity.log"
    echo "== FMA instructions (must be 0): $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)" | tee -a "$OUT/identity.log"
    python3 "$CI/uci_check.py" "$BD/forge" --full 2>&1 | tee -a "$OUT/identity.log" || status=1
    (cd "$BD" && ctest --output-on-failure --timeout 3000) > "$OUT/ctest_$MODE.log" 2>&1
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    ;;
  asan)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
      -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all" > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    (cd "$BD" && ctest --output-on-failure --timeout 6000) > "$OUT/ctest_$MODE.log" 2>&1
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" "$LOGDIR" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    ;;
  tsan)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
      "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer" "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread" > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    (cd "$BD" && ctest --output-on-failure --timeout 6000) > "$OUT/ctest_$MODE.log" 2>&1
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" "$LOGDIR" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    # Job-specific threading stress (e.g. O1): opus_round1/<JOB>/tsan_extra.sh <forge_exe> <out_dir>
    for extra in "$ROOT"/opus_round1/*/tsan_extra.sh; do
      [ -f "$extra" ] || continue
      echo "== $extra" | tee -a "$OUT/tsan_extra.log"
      bash "$extra" "$BD/forge" "$OUT" >> "$OUT/tsan_extra.log" 2>&1 || status=1
    done
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
      echo "TSan reports found:"; cat "$LOGDIR"/* | head -200; status=1
    else
      echo "TSan: 0 reports" | tee -a "$OUT/known_$MODE.log"
    fi
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
# Positive proof of the build configuration: compile flags and instrumentation symbols in forge.
{
  echo "CMAKE_CXX_FLAGS: $(grep -E '^CMAKE_CXX_FLAGS:' "$BD/CMakeCache.txt" | cut -d= -f2-)"
  echo "CMAKE_BUILD_TYPE: $(grep -E '^CMAKE_BUILD_TYPE:' "$BD/CMakeCache.txt" | cut -d= -f2-)"
  echo "FORGE_ENABLE_SANITIZERS: $(grep -E '^FORGE_ENABLE_SANITIZERS:' "$BD/CMakeCache.txt" | cut -d= -f2-)"
  echo "asan symbols in forge: $(nm "$BD/forge" 2>/dev/null | grep -c '__asan_' || true)"
  echo "ubsan symbols in forge: $(nm "$BD/forge" 2>/dev/null | grep -c '__ubsan_' || true)"
  echo "tsan symbols in forge: $(nm "$BD/forge" 2>/dev/null | grep -c '__tsan_' || true)"
} > "$OUT/build_config_$MODE.txt"
cat "$OUT/build_config_$MODE.txt"
echo "run_ci $MODE status=$status"
exit $status
