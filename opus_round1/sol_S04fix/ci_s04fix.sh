#!/usr/bin/env bash
# S04fix Linux evidence for FORGE_ATTACKS_INIT_ONCE=ON (used by .github/workflows/opus-sol-s04fix-ci.yml;
# opus-ci.yml covers the default OFF build). Box flags, g++-14. On Linux GNU the cold first-Board test is the
# TSan variant (forge_sol_S04_cold_tsan_test_20261025) in every mode, and forge_sol_S04_cold_probe runs it in
# 1000 fresh processes (S04-1). Both tests carry their own ctest TIMEOUT (S04-2), which overrides --timeout.
#   release : lock (294dbed) vs default (OFF) build: forge sha256 + disassembly; ON build: AL1 identity
#             (uci_check --full), FMA count, full ctest + known-failure check, cold tests listed with properties
#   asan    : ON + ASan/UBSan (recover off): full ctest + known-failure check
#   tsan    : ON + -fsanitize=thread everywhere: full ctest + known-failure check; RED control: the cold test
#             built WITHOUT the option (the original init-bool race) must fail under TSan (exit 66)
# usage: opus_round1/sol_S04fix/ci_s04fix.sh <release|asan|tsan> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CI="$ROOT/opus_round1/ci"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
status=0
build() {  # build <src> <dir> <build type> <extra cxx flags> [cmake args...]
  local src=$1 dir=$2 type=$3 extra=$4; shift 4
  cmake -S "$src" -B "$dir" -G Ninja -DCMAKE_BUILD_TYPE="$type" -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE_FLAGS $extra" "$@" > "$OUT/configure_$(basename "$dir").log" 2>&1 || exit 1
  cmake --build "$dir" -j"$(nproc)" > "$OUT/build_$(basename "$dir").log" 2>&1 || { tail -50 "$OUT/build_$(basename "$dir").log"; exit 1; }
}
ctest_known() {  # ctest_known <build dir> <tag> [sanitizer log dir]
  (cd "$1" && ctest -N -L cold-init && ctest --show-only=json-v1 -L cold-init > "$OUT/cold_tests_$2.json") 2>&1 | tee "$OUT/cold_tests_$2.log"
  python3 - "$OUT/cold_tests_$2.json" <<'PY' 2>&1 | tee -a "$OUT/cold_tests_$2.log"
import json, sys
for t in json.load(open(sys.argv[1]))["tests"]:
    props = {p["name"]: p["value"] for p in t.get("properties", [])}
    print(t["name"], "TIMEOUT", props.get("TIMEOUT"), "LABELS", props.get("LABELS"), "RUN_SERIAL", props.get("RUN_SERIAL"))
PY
  (cd "$1" && ctest --output-on-failure --timeout 600) 2>&1 | tee "$OUT/ctest_$2.log"
  python3 "$CI/check_known_failures.py" "$OUT/ctest_$2.log" ${3:+"$3"} 2>&1 | tee "$OUT/known_$2.log" || status=1
  grep -q 'forge_sol_S04_cold_tsan_test_20261025 .*Passed' "$OUT/ctest_$2.log" || { echo "cold TSan test did not pass/run"; status=1; }
  grep -q 'forge_sol_S04_cold_probe .*Passed' "$OUT/ctest_$2.log" || { echo "cold probe did not pass/run"; status=1; }
  grep -E 'COLD_PROBE_PASS|COLD_PROBE_FAIL' "$OUT/ctest_$2.log" | tee -a "$OUT/known_$2.log"
}
case "$MODE" in
  release)
    mkdir -p "$OUT/lock_src" && git -C "$ROOT" archive 294dbed | tar -x -m -C "$OUT/lock_src"
    build "$OUT/lock_src" "$OUT/build_lock" Release ""
    build "$ROOT" "$OUT/build_default" Release ""
    build "$ROOT" "$OUT/build_on" Release "" -DFORGE_ATTACKS_INIT_ONCE=ON
    { for t in lock default on; do echo "$t forge sha256 $(sha256sum "$OUT/build_$t/forge" | cut -d' ' -f1) FMA $(objdump -d "$OUT/build_$t/forge" | grep -cE 'vfn?m(add|sub)' || true)"; done
      a=$(sha256sum < "$OUT/build_lock/forge"); b=$(sha256sum < "$OUT/build_default/forge")
      echo "default (OFF) build forge binary vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      a=$(objdump -d "$OUT/build_lock/forge" | tail -n +3 | sha256sum); b=$(objdump -d "$OUT/build_default/forge" | tail -n +3 | sha256sum)
      echo "default (OFF) build disassembly vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      echo "cold targets in the default build: $(cd "$OUT/build_default" && ctest -N -L cold-init | grep -c 'Test #' || true) (must be 0)"
    } 2>&1 | tee "$OUT/identity_default_vs_lock.log"
    grep -q 'disassembly vs lock: IDENTICAL' "$OUT/identity_default_vs_lock.log" || status=1
    python3 "$CI/uci_check.py" "$OUT/build_on/forge" --full 2>&1 | tee "$OUT/identity_on.log"
    grep -q '^ALL OK' "$OUT/identity_on.log" || status=1
    ctest_known "$OUT/build_on" release_on
    ;;
  asan)
    build "$ROOT" "$OUT/build_asan_on" RelWithDebInfo "-fno-sanitize-recover=all" -DFORGE_ENABLE_SANITIZERS=ON -DFORGE_ATTACKS_INIT_ONCE=ON
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:exitcode=66"
    ctest_known "$OUT/build_asan_on" asan_on "$LOGDIR"
    ;;
  tsan)
    build "$ROOT" "$OUT/build_tsan_on" RelWithDebInfo "-fsanitize=thread -fno-omit-frame-pointer" \
      -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -DFORGE_ATTACKS_INIT_ONCE=ON
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    ctest_known "$OUT/build_tsan_on" tsan_on "$LOGDIR"
    # RED control (planted bug = the original code): same test source, option OFF, TSan. Its reports go to a
    # separate directory so they cannot mix with the GREEN evidence above.
    RED="$OUT/red_off_race"; mkdir -p "$RED/tsan_logs"
    $CXX -std=c++20 -O1 -g1 -fsanitize=thread -fno-omit-frame-pointer $BASE_FLAGS -pthread -I"$ROOT/include" \
      "$ROOT/tests/forge_sol_S04_tsan_test_20261025.cpp" "$ROOT/src/bitboard.cpp" "$ROOT/src/board.cpp" \
      -o "$RED/cold_off_race" > "$RED/build.log" 2>&1 || { cat "$RED/build.log"; status=1; }
    red_fail=0
    for i in 1 2 3; do
      TSAN_OPTIONS="log_path=$RED/tsan_logs/run$i:halt_on_error=1:exitcode=66" timeout 120 "$RED/cold_off_race" > "$RED/run$i.out" 2>&1
      rc=$?; echo "RED run $i (option OFF, original init bool): exit $rc" | tee -a "$OUT/red_off_race.log"
      [ "$rc" -ne 0 ] && red_fail=$((red_fail+1))
    done
    grep -h -m1 -A12 'WARNING: ThreadSanitizer' "$RED"/tsan_logs/* 2>/dev/null | sed 's/^/  | /' | head -40 | tee -a "$OUT/red_off_race.log"
    echo "RED control: $red_fail/3 OFF runs failed (expected 3/3)" | tee -a "$OUT/red_off_race.log"
    [ "$red_fail" -eq 3 ] || status=1
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
echo "ci_s04fix $MODE status=$status" | tee -a "$OUT/status_$MODE.log"
exit $status
