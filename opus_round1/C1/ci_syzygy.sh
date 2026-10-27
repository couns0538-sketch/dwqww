#!/usr/bin/env bash
# Job C1 CI (.github/workflows/opus-c1-syzygy.yml): build forge and forge_syzygy_tests in one mode
# and run them against a tablebase folder (the CI caches the 3-4 piece set, ci_fetch_tables.sh).
#   release : CMake Release, box flags
#   asan    : ASan+UBSan, recover off (the test also re-runs everything on exact-size heap copies)
#   tsan    : ThreadSanitizer; the UCI smoke test also searches with Threads 4
# usage: ci_syzygy.sh <release|asan|tsan> <tablebase_dir> [out_dir]
set -uo pipefail
MODE=$1
TB=$(cd "$2" && pwd)
OUT=${3:-ci_out_c1}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
BD="$OUT/build_$MODE"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
case "$MODE" in
  release) EXTRA=(-DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=$BASE_FLAGS") ;;
  asan)
    EXTRA=(-DCMAKE_BUILD_TYPE=RelWithDebInfo -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all")
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1" ;;
  tsan)
    EXTRA=(-DCMAKE_BUILD_TYPE=RelWithDebInfo "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer"
           "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread")
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1" ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
echo "== compiler: $($CXX --version | head -1); tables: $(ls "$TB" | grep -c 'rtb[wz]$') files in $TB"
cmake -S "$ROOT" -B "$BD" -G Ninja -DCMAKE_CXX_COMPILER="$CXX" "-DFORGE_SYZYGY_PATH=$TB" "${EXTRA[@]}" \
  > "$OUT/configure_$MODE.log" 2>&1 || { tail -30 "$OUT/configure_$MODE.log"; exit 1; }
cmake --build "$BD" -j"$(nproc)" --target forge forge_syzygy_tests > "$OUT/build_$MODE.log" 2>&1 \
  || { tail -50 "$OUT/build_$MODE.log"; exit 1; }
status=0
echo "== forge_syzygy_tests ($MODE)"
timeout --kill-after=15 1200 "$BD/forge_syzygy_tests" "$ROOT/tests/syzygy_fixtures.tsv" "$ROOT/tests/syzygy_reference.tsv" "$TB" \
  2>&1 | tee "$OUT/syzygy_tests_$MODE.log"
[ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAIL: forge_syzygy_tests"; status=1; }
for threads in 1 4; do
  echo "== uci_tb_smoke ($MODE, Threads $threads)"
  timeout --kill-after=15 900 python3 "$ROOT/opus_round1/C1/uci_tb_smoke.py" "$BD/forge" "$TB" "$threads" \
    2>&1 | tee -a "$OUT/uci_tb_smoke_$MODE.log"
  [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAIL: uci_tb_smoke Threads $threads"; status=1; }
done
if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
  echo "sanitizer reports found:"; cat "$LOGDIR"/* | head -200; status=1
else
  echo "sanitizer reports: 0" | tee -a "$OUT/syzygy_tests_$MODE.log"
fi
echo "ci_syzygy $MODE status=$status"
exit $status
