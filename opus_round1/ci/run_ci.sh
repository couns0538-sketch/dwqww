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
# opus-smp-layout-20261107 (trial_w6 tree): FORGE_SPD_NNUE_ZMM defaults to 1 and #errors without AVX-512F, which the
# x86-64-v3 runner build does not have -> 0 here (speed-only switch, bit-exact, touches no TT/SMP code). The pack's
# switch is ON so that its tests (tt_lockless, smp_lifecycle) run under release, ASan+UBSan and TSan.
BASE_FLAGS="$BASE_FLAGS -DFORGE_SPD_NNUE_ZMM=0"
PACK_CMAKE="-DFORGE_SMP_LAYOUT=ON"
BD="$OUT/build_$MODE"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
status=0
# opus2 SMP pack (fable bug hunt NIT-2): the pack's own CTests must have run and passed, not merely "no unexpected
# failure" (check_known_failures.py alone stays green if the tests were never built).
# usage: require_pack_tests <ctest log> <log to append to>. Never call it inside a pipeline: it sets status here.
require_pack_tests() {
  local t
  for t in forge_tt_lockless_tests forge_smp_lifecycle_tests; do
    if grep -Eq "Test +#[0-9]+: $t \.+ +Passed" "$1"; then
      echo "pack test $t: Passed" | tee -a "$2"
    else
      echo "FAIL: pack test $t did not run and pass" | tee -a "$2"; status=1
    fi
  done
}
case "$MODE" in
  release)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" $PACK_CMAKE "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    echo "== compiler: $($CXX --version | head -1)" | tee "$OUT/identity.log"
    echo "== forge sha256: $(sha256sum "$BD/forge" | cut -d' ' -f1)" | tee -a "$OUT/identity.log"
    echo "== FMA instructions (must be 0): $(objdump -d "$BD/forge" | grep -cE 'vfn?m(add|sub)' || true)" | tee -a "$OUT/identity.log"
    python3 "$CI/uci_check.py" "$BD/forge" --full 2>&1 | tee -a "$OUT/identity.log" || status=1
    # opus2 SMP pack (R1 review NIT-2 / NIT-1): the ON path's pins on Linux, and the default (macro-0) configuration
    # still built and pinned, so CI keeps checking what it checked before this pack.
    echo "== TtLockless=true (same exe):" | tee -a "$OUT/identity.log"
    python3 "$CI/uci_check.py" "$BD/forge" --full --opt TtLockless=true 2>&1 | tee -a "$OUT/identity.log" || status=1
    # Pins cannot tell an applied node-identical option from an ignored one (fable bug hunt NIT-1): the toggle must
    # empty the table exactly as Clear Hash does, and lockless must equal legacy cold and warm.
    echo "== TtLockless liveness (same exe):" | tee -a "$OUT/identity.log"
    python3 "$ROOT/opus_round1/opus2_smp/liveness_check.py" "$BD/forge" 12 2>&1 | tee -a "$OUT/identity.log" || status=1
    cmake -S "$ROOT" -B "${BD}_macro0" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" > "$OUT/configure_${MODE}_macro0.log" 2>&1 || exit 1
    cmake --build "${BD}_macro0" --target forge -j"$(nproc)" > "$OUT/build_${MODE}_macro0.log" 2>&1 || { tail -50 "$OUT/build_${MODE}_macro0.log"; exit 1; }
    echo "== default build (FORGE_SMP_LAYOUT OFF) forge sha256: $(sha256sum "${BD}_macro0/forge" | cut -d' ' -f1)" | tee -a "$OUT/identity.log"
    # Capture the option lists first: under pipefail a 'grep -q' that exits early could make the engine's SIGPIPE decide.
    uci_m0=$(printf 'uci\nquit\n' | "${BD}_macro0/forge" 2>/dev/null) || { echo "FAIL: macro-0 forge exited non-zero on uci/quit" | tee -a "$OUT/identity.log"; status=1; }
    uci_m1=$(printf 'uci\nquit\n' | "$BD/forge" 2>/dev/null) || { echo "FAIL: macro-1 forge exited non-zero on uci/quit" | tee -a "$OUT/identity.log"; status=1; }
    if grep -q 'TtLockless' <<< "$uci_m0"; then echo "FAIL: macro-0 build advertises TtLockless" | tee -a "$OUT/identity.log"; status=1; else echo "macro-0 build: no TtLockless option (OK)" | tee -a "$OUT/identity.log"; fi
    if grep -q '^option name TtLockless type check default false' <<< "$uci_m1"; then echo "macro-1 build: TtLockless advertised, default false (OK)" | tee -a "$OUT/identity.log"; else echo "FAIL: macro-1 build does not advertise 'TtLockless type check default false'" | tee -a "$OUT/identity.log"; status=1; fi
    python3 "$CI/uci_check.py" "${BD}_macro0/forge" --full 2>&1 | tee -a "$OUT/identity.log" || status=1
    (cd "$BD" && ctest --output-on-failure --timeout 3000) > "$OUT/ctest_$MODE.log" 2>&1
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    require_pack_tests "$OUT/ctest_$MODE.log" "$OUT/known_$MODE.log"
    ;;
  asan)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" $PACK_CMAKE \
      -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all" > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    (cd "$BD" && ctest --output-on-failure --timeout 6000) > "$OUT/ctest_$MODE.log" 2>&1
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" "$LOGDIR" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    require_pack_tests "$OUT/ctest_$MODE.log" "$OUT/known_$MODE.log"
    ;;
  tsan)
    cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" $PACK_CMAKE \
      "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer" "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread" > "$OUT/configure_$MODE.log" 2>&1 || exit 1
    cmake --build "$BD" -j"$(nproc)" > "$OUT/build_$MODE.log" 2>&1 || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    (cd "$BD" && ctest --output-on-failure --timeout 6000) > "$OUT/ctest_$MODE.log" 2>&1
    python3 "$CI/check_known_failures.py" "$OUT/ctest_$MODE.log" "$LOGDIR" 2>&1 | tee "$OUT/known_$MODE.log" || status=1
    require_pack_tests "$OUT/ctest_$MODE.log" "$OUT/known_$MODE.log"
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
echo "run_ci $MODE status=$status"
exit $status
