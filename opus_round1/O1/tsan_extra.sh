#!/usr/bin/env bash
# O1 TSan runs, called by opus_round1/ci/run_ci.sh in tsan mode on the TSan-built forge (TSAN_OPTIONS
# with log_path + halt_on_error is inherited; run_ci.sh fails on any report file).
# Short by design (a few minutes on a 4-vCPU runner; hard cap per test below): 2-4 engine threads,
# depth 8. Every test runs under its own timeout and the running test is printed before it starts and
# on timeout. Engines run under `nice -n 5` so the CI runner agent keeps CPU (the first version of
# this hook ran 200 x depth 12 at up to 8 threads; the runner was starved and lost contact after 52 min).
# The full-size acceptance runs are in .github/workflows/opus-o1-tsan-full.yml (manual, sharded).
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
FORGE=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
python3 -m pip install --quiet --break-system-packages chess 2>/dev/null || python3 -m pip install --quiet chess || true
status=0
run_test() { # name timeout_seconds command...
  local name=$1 limit=$2; shift 2
  echo "== [O1 tsan] $(date +%T) start $name (timeout ${limit}s)"
  timeout --kill-after=10 "$limit" nice -n 5 "$@" > "$OUT/tsan_o1_$name.log" 2>&1
  local rc=$?
  if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
    echo "== [O1 tsan] TIMEOUT in $name after ${limit}s - last output:"; tail -n 20 "$OUT/tsan_o1_$name.log"; status=1
  elif [ $rc -ne 0 ]; then
    echo "== [O1 tsan] FAIL $name (exit $rc):"; tail -n 20 "$OUT/tsan_o1_$name.log"; status=1
  else
    echo "== [O1 tsan] $(date +%T) PASS $name"; tail -n 3 "$OUT/tsan_o1_$name.log"
  fi
}
EPD="$ROOT/tools/openings/forge-10000.epd"
P50="$ROOT/opus_round1/O3/positions50.fen"
run_test smp_depth8_t2_t4 180 python3 -u "$HERE/smp_depth.py" "$FORGE" --positions "$EPD" --count 40 --threads 2,4 \
    --depth 8 --timeout 120 --progress 10
run_test uci_stress_t1_to_t4 240 python3 -u "$HERE/uci_stress.py" "$FORGE" --iterations 120 --seed 20261026 \
    --positions "$P50" --threads 1,2,3,4 --slack 60
run_test smp_depth8_options_t4 120 python3 -u "$HERE/smp_depth.py" "$FORGE" --positions "$EPD" --count 20 --threads 4 \
    --depth 8 --timeout 120 --progress 10 --option SmpExactNodes=true --option SmpBestThread=true
run_test uci_stress_options_toggled_t2_t4 180 python3 -u "$HERE/uci_stress.py" "$FORGE" --iterations 60 --seed 20261027 \
    --positions "$P50" --threads 2,4 --slack 60 --toggle-options
exit $status
