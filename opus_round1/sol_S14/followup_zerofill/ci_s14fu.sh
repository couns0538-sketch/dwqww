#!/usr/bin/env bash
# Linux evidence for the S14 follow-up (FORGE_NOZERO_MOVE_BUFFERS, default off), used by
# .github/workflows/opus-sol-s14fu.yml. Every build uses the box flags (g++-14, x86-64-v3, no FMA contraction).
#   check   : lock (294dbed), switch-off and switch-on builds (CMake Release); uci_check --full for off and on;
#             FMA counts; off-vs-lock binary comparison; ctest of the on build with the known-failure check;
#             pick-order oracle (all patterns, every root and child) and its planted-bug check; codegen compare
#   asan    : on build with ASan+UBSan: ctest + known-failure check, uci_check (bench 11/13/16 + perft),
#             pick-order oracle under ASan+UBSan
#   tsan    : on build with TSan: ctest + known-failure check, uci_check (bench 11/13/16 + perft)
#   profile : callgrind of bench 13 (lock and on, box flags + -g) with per-call-site memset attribution;
#             valgrind memcheck of bench 11 and of the oracle (heap storage) for lock/off and on;
#             clang MemorySanitizer build of the oracle (heap storage) and of the engine (bench 11), best effort
#   nps     : paired ABBA NPS lock vs on (nps_ab.py, fresh processes, 10 runs per side, bench 16 and 20, nodes
#             must match), then the same lock vs a second lock build as an A/A control
# usage: opus_round1/sol_S14/followup_zerofill/ci_s14fu.sh <mode> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_out}
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
CI="$ROOT/opus_round1/ci"
JOB="$ROOT/opus_round1/sol_S14/followup_zerofill"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
LOCK=294dbed3a15dfd821aaf9d4edc6e5f62832fd460
ON="-DFORGE_NOZERO_MOVE_BUFFERS=1"
status=0

configure_build() {  # configure_build <name> <src> <build_type> <cxx_flags> [extra cmake args...] ; builds every target
  local name=$1 src=$2 type=$3 flags=$4; shift 4
  cmake -S "$src" -B "$OUT/build_$name" -G Ninja -DCMAKE_BUILD_TYPE="$type" -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$flags" "$@" > "$OUT/configure_$name.log" 2>&1 || { tail -30 "$OUT/configure_$name.log"; exit 1; }
  cmake --build "$OUT/build_$name" -j"$(nproc)" > "$OUT/build_$name.log" 2>&1 || { tail -60 "$OUT/build_$name.log"; exit 1; }
  echo "$name forge sha256 $(sha256sum "$OUT/build_$name/forge" | cut -d' ' -f1) warnings $(grep -ci 'warning:' "$OUT/build_$name.log")" | tee -a "$OUT/builds.log"
}
lock_src() {
  mkdir -p "$OUT/src_lock"
  # -m: archived files get the current time (ninja loops on future mtimes)
  [ -f "$OUT/src_lock/CMakeLists.txt" ] || git -C "$ROOT" archive "$LOCK" | tar -x -m -C "$OUT/src_lock"
}
ctest_known() {  # ctest_known <name> [sanitizer log dir]
  (cd "$OUT/build_$1" && ctest --output-on-failure --timeout 900) > "$OUT/ctest_$1.log" 2>&1
  python3 "$CI/check_known_failures.py" "$OUT/ctest_$1.log" ${2:-} 2>&1 | tee "$OUT/known_$1.log" || status=1
}
msan_frames() {  # msan_frames <log>: the first stack frame of every MemorySanitizer report, counted
  awk '/WARNING: MemorySanitizer/ {w = 1; next} w && /^ *#0 / {sub(/^ *#0 0x[0-9a-f]+ in /, ""); print; w = 0}' "$1" \
    | sed -E 's/:[0-9]+:[0-9]+$//' | sort | uniq -c | sort -rn
}

case "$MODE" in
  check)
    lock_src
    configure_build lock "$OUT/src_lock" Release "$BASE_FLAGS"
    configure_build off "$ROOT" Release "$BASE_FLAGS"
    configure_build on "$ROOT" Release "$BASE_FLAGS" -DFORGE_NOZERO_MOVE_BUFFERS=ON
    grep -q 'FORGE_NOZERO_MOVE_BUFFERS=1' "$OUT/build_on/build.ninja" || { echo "CMake option did not reach the build"; status=1; }
    for t in lock off on; do
      echo "FMA $t: $(objdump -d "$OUT/build_$t/forge" | grep -cE 'vfn?m(add|sub)' || true)" | tee -a "$OUT/builds.log"
    done
    if cmp -s "$OUT/build_lock/forge" "$OUT/build_off/forge"; then echo "off build is byte-identical to the lock build" | tee -a "$OUT/builds.log"
    else echo "off build differs from the lock build in $(cmp -l "$OUT/build_lock/forge" "$OUT/build_off/forge" | wc -l) bytes" | tee -a "$OUT/builds.log"; fi
    for t in off on; do
      python3 "$CI/uci_check.py" "$OUT/build_$t/forge" --full > "$OUT/identity_$t.log" 2>&1
      if grep -q '^ALL OK' "$OUT/identity_$t.log"; then echo "identity $t: ALL OK"; else echo "identity $t: FAILED"; cat "$OUT/identity_$t.log"; status=1; fi
    done
    ctest_known on
    CXX="$CXX" bash "$JOB/run_picker_oracle.sh" "$ROOT" "$OUT/oracle" "" 100000 > "$OUT/oracle.log" 2>&1 || status=1
    grep -E '^(sw=|MATCH|DIFFER|reference|run_picker)' "$OUT/oracle.log"
    ref=$(grep -oE 'digest [0-9a-f]+' "$OUT/oracle/oracle_sw0_zero.txt" | tail -1 | cut -d' ' -f2)
    python3 "$JOB/mutation_check.py" "$ROOT" "$OUT/mutants" --ref-digest "$ref" --cxx "$CXX" --children 100000 \
      > "$OUT/mutation_check.log" 2>&1 || status=1
    cat "$OUT/mutation_check.log"
    bash "$JOB/codegen_compare_s14.sh" "$OUT/build_lock/forge" "$OUT/build_on/forge" "$OUT/codegen_diffs" > "$OUT/codegen_lock_vs_on.log" 2>&1 || status=1
    bash "$JOB/codegen_compare_s14.sh" "$OUT/build_lock/forge" "$OUT/build_off/forge" > "$OUT/codegen_lock_vs_off.log" 2>&1 || status=1
    cat "$OUT/codegen_lock_vs_on.log"
    ;;
  asan)
    LOGDIR="$OUT/sanitizer_logs_asan"; mkdir -p "$LOGDIR"
    configure_build asan_on "$ROOT" RelWithDebInfo "$BASE_FLAGS -fno-sanitize-recover=all" -DFORGE_ENABLE_SANITIZERS=ON -DFORGE_NOZERO_MOVE_BUFFERS=ON
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    ctest_known asan_on "$LOGDIR"
    python3 "$CI/uci_check.py" "$OUT/build_asan_on/forge" > "$OUT/identity_asan_on.log" 2>&1 || status=1
    cat "$OUT/identity_asan_on.log"
    EXTRA_FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer" PATTERNS="zero random heap" \
      CXX="$CXX" bash "$JOB/run_picker_oracle.sh" "$ROOT" "$OUT/oracle_asan" "" 100000 > "$OUT/oracle_asan.log" 2>&1 || status=1
    grep -E '^(sw=|MATCH|DIFFER|reference|run_picker)' "$OUT/oracle_asan.log"
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then echo "sanitizer reports:"; cat "$LOGDIR"/* | head -100; status=1
    else echo "ASan/UBSan: 0 report files" | tee -a "$OUT/known_asan_on.log"; fi
    ;;
  tsan)
    LOGDIR="$OUT/sanitizer_logs_tsan"; mkdir -p "$LOGDIR"
    configure_build tsan_on "$ROOT" RelWithDebInfo "$BASE_FLAGS -fsanitize=thread -fno-omit-frame-pointer" \
      -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -DFORGE_NOZERO_MOVE_BUFFERS=ON
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    ctest_known tsan_on "$LOGDIR"
    python3 "$CI/uci_check.py" "$OUT/build_tsan_on/forge" > "$OUT/identity_tsan_on.log" 2>&1 || status=1
    cat "$OUT/identity_tsan_on.log"
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then echo "TSan reports:"; cat "$LOGDIR"/* | head -100; status=1
    else echo "TSan: 0 reports" | tee -a "$OUT/known_tsan_on.log"; fi
    ;;
  profile)
    lock_src
    configure_build plock "$OUT/src_lock" Release "$BASE_FLAGS -g"
    configure_build pon "$ROOT" Release "$BASE_FLAGS -g $ON"
    printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench 13\nquit\n' > "$OUT/bench13.txt"
    for t in plock pon; do
      valgrind --tool=callgrind --dump-instr=yes --compress-strings=no --compress-pos=no \
        --callgrind-out-file="$OUT/callgrind_$t.out" "$OUT/build_$t/forge" < "$OUT/bench13.txt" > "$OUT/callgrind_run_$t.log" 2>&1 || status=1
      grep -E 'bench depth|Collected' "$OUT/callgrind_run_$t.log"
      python3 "$JOB/callgrind_callers.py" "$OUT/callgrind_$t.out" --exe "$OUT/build_$t/forge" --json "$OUT/memset_callers_$t.json" \
        > "$OUT/memset_callers_$t.log" 2>&1 || status=1
      head -12 "$OUT/memset_callers_$t.log"
      callgrind_annotate --inclusive=no "$OUT/callgrind_$t.out" 2>/dev/null | head -45 > "$OUT/profile_self_$t.txt"
    done
    printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench 11\nquit\n' > "$OUT/bench11.txt"
    for t in plock pon; do
      valgrind --tool=memcheck --track-origins=yes --error-exitcode=99 --expensive-definedness-checks=yes \
        "$OUT/build_$t/forge" < "$OUT/bench11.txt" > "$OUT/memcheck_bench11_$t.log" 2>&1
      echo "memcheck bench 11 $t: exit $? $(grep -E 'ERROR SUMMARY' "$OUT/memcheck_bench11_$t.log") $(grep -oE 'bench depth 11 nodes [0-9]+' "$OUT/memcheck_bench11_$t.log")"
    done
    RUNNER="valgrind --tool=memcheck --track-origins=yes --error-exitcode=99 --expensive-definedness-checks=yes --log-file=$OUT/memcheck_oracle_%p.log" \
      PATTERNS="heap" CXX="$CXX" bash "$JOB/run_picker_oracle.sh" "$ROOT" "$OUT/oracle_memcheck" "" 300 > "$OUT/oracle_memcheck.log" 2>&1 || status=1
    grep -E '^(sw=|MATCH|DIFFER|reference|run_picker)' "$OUT/oracle_memcheck.log"
    grep -h 'ERROR SUMMARY' "$OUT"/memcheck_oracle_*.log
    # MemorySanitizer (clang), best effort. libstdc++ is not instrumented, so text that libstdc++ fills (input lines,
    # FEN fields) can be reported where forge parses it; those reports are not about the move buffers. What matters is
    # the number of reports whose first frame is in picker or move-list code, lock (switch off) versus on.
    if command -v clang++ > /dev/null; then
      MSAN="-fsanitize=memory -fsanitize-memory-track-origins=2 -fsanitize-recover=memory -fno-omit-frame-pointer"
      export MSAN_OPTIONS=halt_on_error=0
      head -200 "$ROOT/tools/openings/forge-10000.epd" > "$OUT/roots200.epd"
      PATTERNS="heap" CXX=clang++ ARCH_FLAGS="-march=x86-64-v3" LIFETIME_FLAG="" EXTRA_FLAGS="$MSAN" \
        bash "$JOB/run_picker_oracle.sh" "$ROOT" "$OUT/oracle_msan" "$OUT/roots200.epd" 200 > "$OUT/oracle_msan.log" 2>&1
      echo "MSan oracle (clang, heap storage, 212 roots + children) exit $?:"
      grep -E '^(built|sw=|MATCH|DIFFER|reference|run_picker)' "$OUT/oracle_msan.log"
      for sw in 0 1; do
        f="$OUT/oracle_msan/oracle_sw${sw}_heap.err"
        [ -f "$f" ] || continue
        msan_frames "$f" > "$OUT/msan_oracle_sw${sw}_frames.log"
        echo "MSan oracle sw=$sw: reports $(grep -c 'WARNING: MemorySanitizer' "$f")," \
          "first frame in picker/move-list code: $(grep -cE 'MovePicker|MoveList|UninitArray' "$OUT/msan_oracle_sw${sw}_frames.log")"
        head -5 "$OUT/msan_oracle_sw${sw}_frames.log"
      done
      for t in lock on; do
        src=$([ $t = lock ] && echo "$OUT/src_lock" || echo "$ROOT"); def=$([ $t = on ] && echo "$ON" || true)
        # shellcheck disable=SC2086
        clang++ -std=c++20 -O1 -g $MSAN -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -march=x86-64-v3 $def \
          -I"$src/include" "$src"/src/{bitboard,board,book,eval,eval_params,nnue,search,uci}.cpp -pthread \
          -o "$OUT/forge_msan_$t" > "$OUT/build_msan_$t.log" 2>&1 \
          || { echo "MSan engine build $t failed"; tail -20 "$OUT/build_msan_$t.log"; continue; }
        "$OUT/forge_msan_$t" < "$OUT/bench11.txt" > "$OUT/msan_bench11_$t.log" 2>&1
        rc=$?
        msan_frames "$OUT/msan_bench11_$t.log" > "$OUT/msan_bench11_${t}_frames.log"
        echo "MSan engine bench 11 $t: exit $rc reports $(grep -c 'WARNING: MemorySanitizer' "$OUT/msan_bench11_$t.log")," \
          "first frame in picker/move-list code: $(grep -cE 'MovePicker|MoveList|UninitArray' "$OUT/msan_bench11_${t}_frames.log")," \
          "$(grep -oE 'bench depth 11 nodes [0-9]+' "$OUT/msan_bench11_$t.log")"
        head -5 "$OUT/msan_bench11_${t}_frames.log"
      done
    else
      echo "clang++ not found: MSan skipped"
    fi
    ;;
  nps)
    lock_src
    configure_build lock "$OUT/src_lock" Release "$BASE_FLAGS"
    configure_build on "$ROOT" Release "$BASE_FLAGS" -DFORGE_NOZERO_MOVE_BUFFERS=ON
    cp "$OUT/build_lock/forge" "$OUT/forge_lock_copy"
    nproc; lscpu | grep -E 'Model name' | cut -c1-200
    python3 "$JOB/nps_ab.py" "$OUT/build_lock/forge" "$OUT/build_on/forge" 10 16 20 > "$OUT/nps_lock_vs_on.log" 2>&1 || status=1
    grep -E 'B/A|MISMATCH' "$OUT/nps_lock_vs_on.log"
    python3 "$JOB/nps_ab.py" "$OUT/build_lock/forge" "$OUT/forge_lock_copy" 10 16 20 > "$OUT/nps_lock_vs_lock_AA.log" 2>&1 || status=1
    grep -E 'B/A|MISMATCH' "$OUT/nps_lock_vs_lock_AA.log"
    grep -l 'NODE MISMATCH' "$OUT"/nps_*.log && { echo "node mismatch in an NPS run"; status=1; }
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
echo "ci_s14fu $MODE status=$status"
exit $status
