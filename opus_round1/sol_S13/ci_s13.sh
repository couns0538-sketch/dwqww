#!/usr/bin/env bash
# S13 Linux evidence for the build switch FORGE_S13_TT_CHILD_PREFETCH (used by .github/workflows/opus-sol-s13-ci.yml;
# mirrors opus_round1/ci/run_ci.sh, which covers the default build). Box flags, g++-14.
#   release : lock (294dbed), branch default and branch switch-on (CMake Release): default forge binary vs lock
#             (sha256), switch-on AL1 identity with TtChildPrefetch off and on, FMA count, ctest + known-failure
#             check; NPS: switch-on binary off vs on (nps_onoff.py) and lock vs switch-on binary with the option
#             off (nps_ab.py), 10 runs, d16 d20
#   asan    : switch on, ASan+UBSan, recover off: ctest + known check, identity d11/13/16 + perft off and on
#   tsan    : switch on, -fsanitize=thread: ctest + known check, threaded UCI sessions (Threads 2 and 4) with
#             TtChildPrefetch on; every TSan log file must be empty
# usage: opus_round1/sol_S13/ci_s13.sh <release|asan|tsan> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CI="$ROOT/opus_round1/ci"
JOB="$ROOT/opus_round1/sol_S13"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
OPT='option name TtChildPrefetch type check default false'
status=0
build() {  # build <src> <dir> <build type> <extra cxx flags> [cmake args...]
  local src=$1 dir=$2 type=$3 extra=$4; shift 4
  cmake -S "$src" -B "$dir" -G Ninja -DCMAKE_BUILD_TYPE="$type" -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE_FLAGS $extra" "$@" > "$OUT/configure_$(basename "$dir").log" 2>&1 || exit 1
  cmake --build "$dir" -j"$(nproc)" > "$OUT/build_$(basename "$dir").log" 2>&1 || { tail -50 "$OUT/build_$(basename "$dir").log"; exit 1; }
}
ctest_known() {  # ctest_known <build dir> <tag> [sanitizer log dir]
  (cd "$1" && ctest --output-on-failure --timeout 600) 2>&1 | tee "$OUT/ctest_$2.log"
  python3 "$CI/check_known_failures.py" "$OUT/ctest_$2.log" ${3:+"$3"} 2>&1 | tee "$OUT/known_$2.log" || status=1
  (cd "$1" && ./forge_tt_prefetch_probe) 2>&1 | tee "$OUT/probe_$2.log" || status=1
}
identity() {  # identity <exe> <tag> [--full]
  for mode in off on; do
    set_arg=(); [ "$mode" = on ] && set_arg=(--set TtChildPrefetch=true)
    python3 "$JOB/uci_check_opt.py" "$1" ${3:-} --expect-option "$OPT" "${set_arg[@]}" 2>&1 | tee "$OUT/identity_$2_$mode.log"
    grep -q '^ALL OK' "$OUT/identity_$2_$mode.log" || status=1
  done
}
case "$MODE" in
  release)
    mkdir -p "$OUT/lock_src" && git -C "$ROOT" archive 294dbed | tar -x -m -C "$OUT/lock_src"
    build "$OUT/lock_src" "$OUT/build_lock" Release "" ; build "$ROOT" "$OUT/build_default" Release ""
    build "$ROOT" "$OUT/build_on" Release "" -DFORGE_S13_TT_CHILD_PREFETCH=ON
    { for t in lock default on; do echo "$t forge sha256 $(sha256sum "$OUT/build_$t/forge" | cut -d' ' -f1) FMA $(objdump -d "$OUT/build_$t/forge" | grep -cE 'vfn?m(add|sub)' || true)"; done
      a=$(sha256sum < "$OUT/build_lock/forge"); b=$(sha256sum < "$OUT/build_default/forge")
      echo "default build forge binary vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      a=$(objdump -d "$OUT/build_lock/forge" | tail -n +3 | sha256sum); b=$(objdump -d "$OUT/build_default/forge" | tail -n +3 | sha256sum)
      echo "default build disassembly vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
    } 2>&1 | tee "$OUT/identity_default_vs_lock.log"
    python3 "$CI/uci_check.py" "$OUT/build_lock/forge" --full 2>&1 | tee "$OUT/identity_lock.log"
    identity "$OUT/build_on/forge" switch_on --full
    ctest_known "$OUT/build_on" release_switch_on
    export MACHINE_EXCLUSIVE='no (GitHub-hosted runner VM: this job alone on the VM, physical host shared)'
    python3 "$JOB/nps_onoff.py" "$OUT/build_on/forge" 10 TtChildPrefetch 16 20 2>&1 | tee "$OUT/nps_onoff_s13.log"
    python3 "$JOB/nps_ab.py" "$OUT/build_lock/forge" "$OUT/build_on/forge" 10 16 20 2>&1 | tee "$OUT/nps_ab_lock_vs_s13on_off.log"
    ;;
  asan)
    build "$ROOT" "$OUT/build_asan_on" RelWithDebInfo "-fno-sanitize-recover=all" -DFORGE_ENABLE_SANITIZERS=ON -DFORGE_S13_TT_CHILD_PREFETCH=ON
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    ctest_known "$OUT/build_asan_on" asan_switch_on "$LOGDIR"
    identity "$OUT/build_asan_on/forge" asan_switch_on
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
      echo "sanitizer reports found:"; cat "$LOGDIR"/* | head -200; status=1
    else
      echo "ASan/UBSan: 0 reports (ctest, probe and identity runs)" | tee -a "$OUT/known_asan_switch_on.log"
    fi
    ;;
  tsan)
    build "$ROOT" "$OUT/build_tsan_on" RelWithDebInfo "-fsanitize=thread -fno-omit-frame-pointer" \
      -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -DFORGE_S13_TT_CHILD_PREFETCH=ON
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    ctest_known "$OUT/build_tsan_on" tsan_switch_on "$LOGDIR"
    for threads in 2 4; do
      echo "== threaded session, Threads $threads, TtChildPrefetch on" | tee -a "$OUT/tsan_sessions.log"
      timeout --kill-after=15 600 python3 "$JOB/uci_threads_session.py" "$OUT/build_tsan_on/forge" "$threads" 10 1000 2>&1 | tee -a "$OUT/tsan_sessions.log"
      [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
    done
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
      echo "TSan reports found:"; cat "$LOGDIR"/* | head -200; status=1
    else
      echo "TSan: 0 reports" | tee -a "$OUT/known_tsan_switch_on.log"
    fi
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
echo "ci_s13 $MODE status=$status" | tee -a "$OUT/status_$MODE.log"
exit $status
