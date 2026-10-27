#!/usr/bin/env bash
# O1-LTT TSan runs (UCI LocklessTT), called by opus_round1/ci/run_ci.sh in tsan mode on the TSan-built forge
# (TSAN_OPTIONS with log_path + halt_on_error is inherited; run_ci.sh fails on any report file).
# Short by design, like the O1 hook: 2-4 engine threads, depth 8, each test under its own timeout,
# engines under `nice -n 5`. The TT-level stress (Threads 2/4/8, 10M operations) is in
# .github/workflows/opus-o1-ltt.yml.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
FORGE=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
O1="$ROOT/opus_round1/O1"
python3 -m pip install --quiet --break-system-packages chess 2>/dev/null || python3 -m pip install --quiet chess || true
status=0
run_test() { # name timeout_seconds command...
  local name=$1 limit=$2; shift 2
  echo "== [O1-LTT tsan] $(date +%T) start $name (timeout ${limit}s)"
  timeout --kill-after=10 "$limit" nice -n 5 "$@" > "$OUT/tsan_ltt_$name.log" 2>&1
  local rc=$?
  if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
    echo "== [O1-LTT tsan] TIMEOUT in $name after ${limit}s - last output:"; tail -n 20 "$OUT/tsan_ltt_$name.log"; status=1
  elif [ $rc -ne 0 ]; then
    echo "== [O1-LTT tsan] FAIL $name (exit $rc):"; tail -n 20 "$OUT/tsan_ltt_$name.log"; status=1
  else
    echo "== [O1-LTT tsan] $(date +%T) PASS $name"; tail -n 3 "$OUT/tsan_ltt_$name.log"
  fi
}
EPD="$ROOT/tools/openings/forge-10000.epd"
P50="$ROOT/opus_round1/O3/positions50.fen"
run_test smp_depth8_lockless_t2_t4 180 python3 -u "$O1/smp_depth.py" "$FORGE" --positions "$EPD" --count 40 --threads 2,4 \
    --depth 8 --timeout 120 --progress 10 --option LocklessTT=true
run_test uci_stress_lockless_toggled_t2_t4 180 python3 -u "$O1/uci_stress.py" "$FORGE" --iterations 60 --seed 20261028 \
    --positions "$P50" --threads 2,4 --slack 60 --toggle-options
exit $status
