#!/usr/bin/env bash
# S12 follow-up on Linux: Sol's null-edge accumulator alias (build switch FORGE_NNUE_LAZY_ACC + UCI NnueLazyAcc, both
# default off). opus-ci.yml covers the default build; this covers the switch. Box flags, g++-14. Pattern of
# opus-sol-S13's ci_s13.sh.
#   release : lock (294dbed), branch default and branch switch-on (CMake Release): default forge binary and
#             disassembly vs lock, switch-on AL1 identity with NnueLazyAcc off and on, FMA, ctest + known-failure
#             check (forge_s12_lazyacc_tests and forge_s12_lazyacc_extra_tests must pass), alias activity per
#             bench depth (alias_stats.py), hot-function
#             sizes; NPS (nps_ab_opts.py, ABBA, 10 runs per side, d16 d20): lock vs switch-on with the option off,
#             switch-on off vs on (same binary), lock vs switch-on with the option on
#   asan    : switch on, ASan+UBSan, recover off: ctest + known check, identity d11/13/16 + perft off and on,
#             alias_stats d13
#   tsan    : switch on, -fsanitize=thread: ctest + known check, threaded UCI sessions (Threads 2 and 4) with
#             NnueLazyAcc on; every TSan log file must be empty
# usage: opus_round1/sol_S12/followup_nullalias/ci_s12_alias.sh <release|asan|tsan> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_out}
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
CI="$ROOT/opus_round1/ci"
JOB="$ROOT/opus_round1/sol_S12/followup_nullalias"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
OPT='option name NnueLazyAcc type check default false'
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
  for t in forge_s12_lazyacc_tests forge_s12_lazyacc_extra_tests; do
    grep -qE "$t \.+ +Passed" "$OUT/ctest_$2.log" || { echo "$t did not pass in $2"; status=1; }
  done
}
identity() {  # identity <exe> <tag> [--full]
  for mode in off on; do
    set_arg=(); [ "$mode" = on ] && set_arg=(--set NnueLazyAcc=true)
    python3 "$JOB/uci_check_opt.py" "$1" ${3:-} --expect-option "$OPT" "${set_arg[@]}" 2>&1 | tee "$OUT/identity_$2_$mode.log"
    grep -q '^ALL OK' "$OUT/identity_$2_$mode.log" || status=1
  done
}
case "$MODE" in
  release)
    mkdir -p "$OUT/lock_src" && git -C "$ROOT" archive 294dbed | tar -x -m -C "$OUT/lock_src"
    build "$OUT/lock_src" "$OUT/build_lock" Release "" ; build "$ROOT" "$OUT/build_default" Release ""
    build "$ROOT" "$OUT/build_on" Release "" -DFORGE_NNUE_LAZY_ACC=ON
    { for t in lock default on; do echo "$t forge sha256 $(sha256sum "$OUT/build_$t/forge" | cut -d' ' -f1) FMA $(objdump -d "$OUT/build_$t/forge" | grep -cE 'vfn?m(add|sub)' || true)"; done
      a=$(sha256sum < "$OUT/build_lock/forge"); b=$(sha256sum < "$OUT/build_default/forge")
      echo "default build forge binary vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      a=$(objdump -d "$OUT/build_lock/forge" | tail -n +3 | sha256sum); b=$(objdump -d "$OUT/build_default/forge" | tail -n +3 | sha256sum)
      echo "default build disassembly vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
    } 2>&1 | tee "$OUT/identity_default_vs_lock.log"
    grep -q 'disassembly vs lock: IDENTICAL' "$OUT/identity_default_vs_lock.log" || status=1
    python3 "$CI/uci_check.py" "$OUT/build_lock/forge" --full 2>&1 | tee "$OUT/identity_lock.log"
    identity "$OUT/build_on/forge" switch_on --full
    ctest_known "$OUT/build_on" release_switch_on
    python3 "$JOB/alias_stats.py" "$OUT/build_on/forge" 13 16 20 2>&1 | tee "$OUT/alias_stats_release.log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
    for t in lock on; do
      nm -S --size-sort -C "$OUT/build_$t/forge" | grep -E ' forge::(Worker::(search|qsearch|static_evaluate|static_evaluate_lazy|record_move|record_null_move)|nnue::(update|evaluate|refresh))\(' | sed "s/^/$t /"
    done > "$OUT/hot_function_sizes.log" 2>&1
    export MACHINE_EXCLUSIVE='no (GitHub-hosted runner VM: this job alone on the VM, physical host shared)'
    python3 "$JOB/nps_ab_opts.py" "$OUT/build_lock/forge" "$OUT/build_on/forge" 10 16 20 2>&1 | tee "$OUT/nps_lock_vs_on_optoff.log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
    python3 "$JOB/nps_ab_opts.py" --opts-b NnueLazyAcc=true "$OUT/build_on/forge" "$OUT/build_on/forge" 10 16 20 2>&1 | tee "$OUT/nps_on_optoff_vs_opton.log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
    python3 "$JOB/nps_ab_opts.py" --opts-b NnueLazyAcc=true "$OUT/build_lock/forge" "$OUT/build_on/forge" 10 16 20 2>&1 | tee "$OUT/nps_lock_vs_on_opton.log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
    ;;
  asan)
    build "$ROOT" "$OUT/build_asan_on" RelWithDebInfo "-fno-sanitize-recover=all" -DFORGE_ENABLE_SANITIZERS=ON -DFORGE_NNUE_LAZY_ACC=ON
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    ctest_known "$OUT/build_asan_on" asan_switch_on "$LOGDIR"
    identity "$OUT/build_asan_on/forge" asan_switch_on
    python3 "$JOB/alias_stats.py" "$OUT/build_asan_on/forge" 13 2>&1 | tee "$OUT/alias_stats_asan.log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
      echo "sanitizer reports found:"; cat "$LOGDIR"/* | head -200; status=1
    else
      echo "ASan/UBSan: 0 reports (ctest, identity and alias_stats runs)" | tee -a "$OUT/known_asan_switch_on.log"
    fi
    ;;
  tsan)
    build "$ROOT" "$OUT/build_tsan_on" RelWithDebInfo "-fsanitize=thread -fno-omit-frame-pointer" \
      -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -DFORGE_NNUE_LAZY_ACC=ON
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    ctest_known "$OUT/build_tsan_on" tsan_switch_on "$LOGDIR"
    for threads in 2 4; do
      echo "== threaded session, Threads $threads, NnueLazyAcc on" | tee -a "$OUT/tsan_sessions.log"
      timeout --kill-after=15 600 python3 "$JOB/uci_threads_session_s12.py" "$OUT/build_tsan_on/forge" "$threads" 10 1000 2>&1 | tee -a "$OUT/tsan_sessions.log"
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
echo "ci_s12_alias $MODE status=$status" | tee -a "$OUT/status_$MODE.log"
exit $status
