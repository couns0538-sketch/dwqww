#!/usr/bin/env bash
# S08fix Linux evidence for FORGE_PROF=ON (used by .github/workflows/opus-sol-s08fix-ci.yml; opus-ci.yml covers the
# default OFF build). Box flags, g++-14.
#   release : lock (294dbed) vs default OFF build (forge binary + disassembly); ON build: AL1 identity
#             (uci_check --full), bench_prof d11..d22 node pins, FMA, full ctest (incl. forge_prof_tests) + known
#             check; NPS on the runner (S08-3): lock bench / OFF bench / ON bench (counters inactive) / ON
#             bench_prof, 10 runs, d16 d20; S08-2 skew: Threads 4 and 1 Profile on/off NPS ratio, Sol's
#             shared-bank build (990cbb18) vs the per-worker build
#   asan    : ON + ASan/UBSan (recover off): full ctest + known check, bench_prof d11/d13, Threads 2 profiled search
#   tsan    : ON + TSan: full ctest + known check (forge_prof_tests runs Threads 1/2/4 profiled searches), plus a
#             Threads 4 profiled UCI search; every TSan log must be empty
# usage: opus_round1/sol_S08fix/ci_s08fix.sh <release|asan|tsan> [out_dir]
set -uo pipefail
MODE=$1
OUT=${2:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CI="$ROOT/opus_round1/ci"
JOB="$ROOT/opus_round1/sol_S08fix"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
LOGDIR="$OUT/sanitizer_logs_$MODE"
mkdir -p "$LOGDIR"
status=0
PINS="11:312866 13:862329 16:3024920 20:12389307 22:34048354"
KIWI="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

build() {  # build <src> <dir> <build type> <extra cxx flags> [cmake args...]
  local src=$1 dir=$2 type=$3 extra=$4; shift 4
  cmake -S "$src" -B "$dir" -G Ninja -DCMAKE_BUILD_TYPE="$type" -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE_FLAGS $extra" "$@" > "$OUT/configure_$(basename "$dir").log" 2>&1 || exit 1
  cmake --build "$dir" -j"$(nproc)" > "$OUT/build_$(basename "$dir").log" 2>&1 || { tail -50 "$OUT/build_$(basename "$dir").log"; exit 1; }
}

ctest_known() {  # ctest_known <build dir> <tag> [sanitizer log dir]
  (cd "$1" && ctest --output-on-failure --timeout 600) 2>&1 | tee "$OUT/ctest_$2.log"
  python3 "$CI/check_known_failures.py" "$OUT/ctest_$2.log" ${3:+"$3"} 2>&1 | tee "$OUT/known_$2.log" || status=1
  grep -q 'forge_prof_tests .*Passed' "$OUT/ctest_$2.log" || { echo "forge_prof_tests did not pass/run"; status=1; }
}

bench_prof_pins() {  # bench_prof_pins <exe> <tag> <depths...>
  local exe=$1 tag=$2 d want got packet pnodes ok; shift 2
  for d in "$@"; do
    want=""
    for p in $PINS; do [ "${p%%:*}" = "$d" ] && want=${p##*:}; done
    printf 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench_prof %s\nquit\n' "$d" \
      | "$exe" > "$OUT/bench_prof_${tag}_d$d.txt" 2>&1
    got=$(sed -n "s/.*bench depth $d nodes \([0-9]*\).*/\1/p" "$OUT/bench_prof_${tag}_d$d.txt")
    packet=$(grep -c '^info string prof schema 1' "$OUT/bench_prof_${tag}_d$d.txt")
    pnodes=$(sed -n 's/^info string prof nodes count \([0-9]*\) .*/\1/p' "$OUT/bench_prof_${tag}_d$d.txt")
    ok=FAIL
    if [ "$got" = "$want" ] && [ "$packet" = 1 ] && [ "$pnodes" = "$want" ]; then ok=OK; fi
    echo "bench_prof d$d nodes $got ref $want counter packet $packet prof nodes $pnodes $ok" | tee -a "$OUT/bench_prof_$tag.log"
    [ "$ok" = OK ] || status=1
  done
}

threaded() {  # threaded <exe> <threads> <tag>
  local exe=$1 threads=$2 tag=$3 rc bm pk
  {
    printf 'uci\nsetoption name Threads value %s\nsetoption name Hash value 16\n' "$threads"
    printf 'setoption name OwnBook value false\nsetoption name Profile value true\nisready\n'
    printf 'position startpos\ngo depth 12\nisready\n'
    printf 'position fen %s\ngo movetime 2000\nisready\nquit\n' "$KIWI"
  } | timeout 600 "$exe" > "$OUT/threaded_$tag.txt" 2>&1
  rc=$?
  bm=$(grep -c '^bestmove' "$OUT/threaded_$tag.txt")
  pk=$(grep -c '^info string prof schema 1' "$OUT/threaded_$tag.txt")
  echo "threaded $tag (Threads $threads, Profile true): exit $rc bestmoves $bm counter packets $pk" | tee -a "$OUT/threaded.log"
  [ "$rc" = 0 ] && [ "$bm" = 2 ] && [ "$pk" = 2 ] || status=1
}

case "$MODE" in
  release)
    mkdir -p "$OUT/lock_src" && git -C "$ROOT" archive 294dbed | tar -x -m -C "$OUT/lock_src"
    mkdir -p "$OUT/sol_src" && git -C "$ROOT" archive 990cbb18 | tar -x -m -C "$OUT/sol_src"
    build "$OUT/lock_src" "$OUT/build_lock" Release ""
    build "$ROOT" "$OUT/build_default" Release ""
    build "$ROOT" "$OUT/build_on" Release "" -DFORGE_PROF=ON
    build "$OUT/sol_src" "$OUT/build_sol_on" Release "" -DFORGE_PROF=ON
    {
      for t in lock default on sol_on; do
        echo "$t forge sha256 $(sha256sum "$OUT/build_$t/forge" | cut -d' ' -f1) FMA $(objdump -d "$OUT/build_$t/forge" | grep -cE 'vfn?m(add|sub)' || true)"
      done
      a=$(sha256sum < "$OUT/build_lock/forge"); b=$(sha256sum < "$OUT/build_default/forge")
      echo "default (OFF) build forge binary vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      a=$(objdump -d "$OUT/build_lock/forge" | tail -n +3 | sha256sum); b=$(objdump -d "$OUT/build_default/forge" | tail -n +3 | sha256sum)
      echo "default (OFF) build disassembly vs lock: $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      echo "forge::prof symbols in the OFF build: $(nm -C "$OUT/build_default/forge" | grep -c 'forge::prof::' || true) (must be 0)"
    } 2>&1 | tee "$OUT/identity_default_vs_lock.log"
    grep -q 'disassembly vs lock: IDENTICAL' "$OUT/identity_default_vs_lock.log" || status=1
    python3 "$CI/uci_check.py" "$OUT/build_on/forge" --full 2>&1 | tee "$OUT/identity_on.log"
    grep -q '^ALL OK' "$OUT/identity_on.log" || status=1
    bench_prof_pins "$OUT/build_on/forge" on 11 13 16 20 22
    ctest_known "$OUT/build_on" release_on
    export MACHINE_EXCLUSIVE='no (GitHub-hosted runner VM: this job alone on the VM, physical host shared)'
    python3 "$JOB/nps_prof_ab.py" --runs 10 --depth 16 --depth 20 --arm lock="$OUT/build_lock/forge" \
      --arm off="$OUT/build_default/forge" --arm on_inactive="$OUT/build_on/forge" \
      --arm on_counting="$OUT/build_on/forge@bench_prof" 2>&1 | tee "$OUT/nps_s08_3.log"
    [ "${PIPESTATUS[0]}" = 0 ] || status=1
    for t in 4 1; do
      python3 "$JOB/prof_threads_nps.py" --threads $t --movetime-ms 3000 --runs 3 \
        --arm sol_shared_bank="$OUT/build_sol_on/forge" --arm per_worker_banks="$OUT/build_on/forge" 2>&1 \
        | tee "$OUT/nps_threads${t}_skew.log"
      [ "${PIPESTATUS[0]}" = 0 ] || status=1
    done
    ;;
  asan)
    build "$ROOT" "$OUT/build_asan_on" RelWithDebInfo "-fno-sanitize-recover=all" -DFORGE_ENABLE_SANITIZERS=ON -DFORGE_PROF=ON
    export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
    export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
    ctest_known "$OUT/build_asan_on" asan_on "$LOGDIR"
    bench_prof_pins "$OUT/build_asan_on/forge" asan_on 11 13
    threaded "$OUT/build_asan_on/forge" 2 asan_t2
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
      echo "sanitizer reports found:"; cat "$LOGDIR"/* | head -200; status=1
    else
      echo "ASan/UBSan: 0 reports (ctest, bench_prof, threaded search)" | tee -a "$OUT/known_asan_on.log"
    fi
    ;;
  tsan)
    build "$ROOT" "$OUT/build_tsan_on" RelWithDebInfo "-fsanitize=thread -fno-omit-frame-pointer" \
      -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -DFORGE_PROF=ON
    export TSAN_OPTIONS="log_path=$LOGDIR/tsan:halt_on_error=1:second_deadlock_stack=1"
    ctest_known "$OUT/build_tsan_on" tsan_on "$LOGDIR"
    threaded "$OUT/build_tsan_on/forge" 4 tsan_t4
    if [ -n "$(find "$LOGDIR" -type f -size +0 2>/dev/null)" ]; then
      echo "TSan reports found:"; cat "$LOGDIR"/* | head -200; status=1
    else
      echo "TSan: 0 reports (ctest incl. forge_prof_tests Threads 1/2/4, Threads 4 profiled UCI search)" | tee -a "$OUT/known_tsan_on.log"
    fi
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
echo "ci_s08fix $MODE status=$status" | tee -a "$OUT/status_$MODE.log"
exit $status
