#!/usr/bin/env bash
# Runs one suite of the Fable/Opus checks on a GitHub runner (Opus, 2026-11-15).
#   bash run_suite.sh <suite> <engine source: the forge-combo29 folder> <results dir>
# suite: perft | mates | badinput | tsan
# The engine source is only built (build.sh) and the engine run; nothing else from it is executed.
# Exit code: 0 = the suite found nothing; 1 = findings (see <results>/summary.txt); 2 = the check itself failed
# (build error, positive control not reported, script error). Every case leaves text evidence in <results>.
set -uo pipefail
suite="$1"; src="$(cd "$2" && pwd)"; res="$3"
here="$(cd "$(dirname "$0")" && pwd)"
py="${PYTHON:-python3}"
work="${RUNNER_TEMP:-/tmp}/forge-ci-$suite"
mkdir -p "$res" "$work"
# A first line at once (Fable's point, 2026-11-15 09:34): if the run stops before the suite has written its own
# summary (a build error, a crash of a script), this line is what arrives, and the logs next to it say where.
echo "suite $suite started $(date -u '+%F %T') UTC; if this is the only line, the run ended before the suite's own summary (see build-*.log, setup files)" > "$res/summary.txt"
{
  echo "suite: $suite"
  echo "date (UTC): $(date -u '+%F %T')"
  echo "engine source: $src"
  echo "engine commit: ${ENGINE_COMMIT:-unknown}"
  echo "machine: $(uname -srm), $(nproc) processors"
  grep -m1 'model name' /proc/cpuinfo || true
  echo "cpu flags present: $(grep -o -w -E 'avx2|avx512f|avx512bw|bmi2' /proc/cpuinfo | sort -u | tr '\n' ' ')"
  echo "compiler: $(g++ --version | head -n 1)"
  echo "cmake: $(cmake --version | head -n 1)"
  echo "python: $("$py" --version 2>&1); python-chess $("$py" -c 'import chess; print(chess.__version__)' 2>&1)"
} > "$res/environment.txt" 2>&1

build() {  # build <kind>
  if ! bash "$here/build.sh" "$1" "$src" "$work/build-$1"; then
    cp "$work/build-$1".*.log "$work/build-$1.info.txt" "$res/" 2>/dev/null || true
    echo "BUILD FAILED ($1)" | tee -a "$res/summary.txt"
    exit 2
  fi
  cp "$work/build-$1.info.txt" "$res/build-$1.info.txt"
  tail -n 40 "$work/build-$1.build.log" > "$res/build-$1.build-tail.log"
}

rc=0
case "$suite" in
  perft)
    build release
    "$py" "$here/perft_suite.py" "$work/build-release/forge" "$res" 25 > "$res/stdout.txt" 2>&1 || rc=$?
    ;;
  mates)
    build release
    "$py" "$here/mates.py" "$work/build-release/forge" "$res" > "$res/stdout.txt" 2>&1 || rc=$?
    ;;
  badinput)
    build asan
    export ASAN_OPTIONS="detect_leaks=1:halt_on_error=1" UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1"
    if ! "$py" "$here/controls.py" asan "$work/build-asan/san_control" "$res/positive_control.txt"; then
      echo "positive control FAILED: no result of this job counts" > "$res/summary.txt"
      rc=2
    else
      "$py" "$here/bad_input.py" "$work/build-asan/forge" "$res" > "$res/stdout.txt" 2>&1 || rc=$?
    fi
    ;;
  tsan)
    build tsan
    export TSAN_OPTIONS="halt_on_error=0 second_deadlock_stack=1 history_size=4"
    if ! "$py" "$here/controls.py" tsan "$work/build-tsan/san_control" "$res/positive_control.txt"; then
      echo "positive control FAILED: no result of this job counts" > "$res/summary.txt"
      rc=2
    else
      "$py" "$here/forge_v3_random.py" random "$work/random_h512.fnn3" 512 1 > "$res/net_file.txt" 2>&1
      sha256sum "$work/random_h512.fnn3" >> "$res/net_file.txt"
      "$py" "$here/tsan_campaign.py" "$work/build-tsan/forge" "$work/random_h512.fnn3" "$res" 140 \
        > "$res/stdout.txt" 2>&1 || rc=$?
    fi
    ;;
  *)
    echo "unknown suite $suite" > "$res/summary.txt"
    rc=2
    ;;
esac
"$py" "$here/cap_logs.py" "$res" || true
echo "suite $suite ended with exit code $rc" >> "$res/environment.txt"
exit "$rc"
