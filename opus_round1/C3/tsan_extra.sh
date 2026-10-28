#!/usr/bin/env bash
# C3 TSan runs (called by opus_round1/ci/run_ci.sh in tsan mode on the TSan-built forge): short UCI
# runs with HardDeadline on, so the watchdog thread races the search threads on almost every move.
# Kept short (well under 10 min, 2-3 threads, short searches); every test has its own timeout and
# the running test is printed before it starts and on timeout.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
FORGE=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
python3 -m pip install --quiet --break-system-packages chess 2>/dev/null || python3 -m pip install --quiet chess || true
status=0
run_test() { # name timeout_seconds command...
  local name=$1 limit=$2; shift 2
  echo "== [C3 tsan] start $name (timeout ${limit}s)"
  timeout --kill-after=10 "$limit" "$@" > "$OUT/tsan_c3_$name.log" 2>&1
  local rc=$?
  if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
    echo "== [C3 tsan] TIMEOUT in $name after ${limit}s - last output:"; tail -n 20 "$OUT/tsan_c3_$name.log"; status=1
  elif [ $rc -ne 0 ]; then
    echo "== [C3 tsan] FAIL $name (exit $rc):"; tail -n 20 "$OUT/tsan_c3_$name.log"; status=1
  else
    echo "== [C3 tsan] PASS $name"; tail -n 2 "$OUT/tsan_c3_$name.log"
  fi
}
# Watchdog vs search on short movetimes (overshoot is not judged under TSan, only missing/duplicate bestmoves).
run_test latency_hd1_t2 240 python3 "$ROOT/tools/latency_test.py" "$FORGE" --suite "$ROOT/tools/wac300.epd" --count 20 \
    --movetimes 20,100 --passes 1 --threads 2 --option HardDeadline=1 --limit-ms 100000 --timeout 60
# Ponder/ponderhit/stop/clock races with the watchdog at a 1 ms grace. The starved scenarios need the
# DebugSearchDelayMs hook, which release-type builds no longer contain: use the test-only target built
# next to forge (CMake target forge_debughooks), with forge as the perft reference.
HOOKS="$(dirname "$FORGE")/forge_debughooks"
if [ ! -x "$HOOKS" ]; then
  echo "== [C3 tsan] FAIL: $HOOKS missing (test-only target with the DebugSearchDelayMs hook)"; exit 1
fi
run_test hard_deadline_regression_t3 240 python3 "$ROOT/tools/hard_deadline_regression.py" "$HOOKS" --iterations 150 --threads 3 --grace 1 --slack 60 --reference "$FORGE"
exit $status
