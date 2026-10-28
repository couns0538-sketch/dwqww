#!/usr/bin/env bash
# Linux evidence for an Opus job branch (used by .github/workflows/opus-ci.yml, also runnable on the box).
#   release : box recipe (g++-14, CMake Release, x86-64-v3, no FMA contraction) -> bench x5 + perft +
#             kiwipete (uci_check --full), FMA count, ctest with the known-failure check
#   asan    : -DFORGE_ENABLE_SANITIZERS=ON (ASan+UBSan), recover off, ctest + known-failure check
#   tsan    : -fsanitize=thread, ctest + known-failure check, then opus_round1/*/tsan_extra.sh if present
# usage: opus_round1/ci/run_ci.sh <release|asan|tsan> [out_dir]
# EXTRA_CMAKE_ARGS (optional, R3): more -D options for every configure step, e.g. the build switches
# (.github/workflows/opus-r3-switches.yml); unset = the default configuration.
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
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" ${EXTRA_CMAKE_ARGS:-} > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    echo "== compiler: $($CXX --version | head -1)" | tee "$OUT/identity.log"
    echo "== forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)" | tee -a "$OUT/identity.log"
    echo "== FMA instructions (must be 0): $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)" | tee -a "$OUT/identity.log"
    python3 "$CI/uci_check.py" "$BD/forge" --full 2>&1 | tee -a "$OUT/identity.log" || status=1
    (cd "$BD" && ctest --output-on-failure --timeout 600) 2>&1 | tee "$OUT/ctest_$MODE.log"
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    ;;
  asan)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
      -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all" ${EXTRA_CMAKE_ARGS:-} > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    (cd "$BD" && ctest --output-on-failure --timeout 600) 2>&1 | tee "$OUT/ctest_$MODE.log"
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" "$LOGDIR" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    ;;
  tsan)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
      "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer" "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread" ${EXTRA_CMAKE_ARGS:-} > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    # Per-test timeout (ctest names a test that times out); output streamed to the job log.
    (cd "$BD" && ctest --output-on-failure --timeout 600) 2>&1 | tee "$OUT/ctest_$MODE.log"
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" "$LOGDIR" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    # Job-specific threading stress (e.g. O1, C3): opus_round1/<JOB>/tsan_extra.sh <forge_exe> <out_dir>.
    # Each hook has its own time limit; the running hook is printed before it starts and on timeout.
    for extra in "$ROOT"/opus_round1/*/tsan_extra.sh; do
      [ -f "$extra" ] || continue
      limit=${TSAN_EXTRA_TIMEOUT:-900}
      echo "== running $extra (limit ${limit}s)" | tee -a "$OUT/tsan_extra.log"
      timeout --kill-after=15 "$limit" bash "$extra" "$BD/forge" "$OUT" 2>&1 | tee -a "$OUT/tsan_extra.log"
      rc=${PIPESTATUS[0]}
      if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
        echo "== TIMEOUT: $extra did not finish within ${limit}s" | tee -a "$OUT/tsan_extra.log"; status=1
      elif [ "$rc" -ne 0 ]; then
        echo "== FAIL: $extra exit $rc" | tee -a "$OUT/tsan_extra.log"; status=1
      fi
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
  echo "EXTRA_CMAKE_ARGS: ${EXTRA_CMAKE_ARGS:-<none>}"
  echo "FORGE_ENABLE_SANITIZERS: $(grep -E '^FORGE_ENABLE_SANITIZERS:' "$BD/CMakeCache.txt" | cut -d= -f2-)"
  echo "asan symbols in forge: $(nm "$BD/forge" 2>/dev/null | grep -c '__asan_' || true)"
  echo "ubsan symbols in forge: $(nm "$BD/forge" 2>/dev/null | grep -c '__ubsan_' || true)"
  echo "tsan symbols in forge: $(nm "$BD/forge" 2>/dev/null | grep -c '__tsan_' || true)"
} > "$OUT/build_config_$MODE.txt"
cat "$OUT/build_config_$MODE.txt"
echo "run_ci $MODE status=$status"
exit $status
