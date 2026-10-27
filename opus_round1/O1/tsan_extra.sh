#!/usr/bin/env bash
# O1 TSan acceptance runs, called by opus_round1/ci/run_ci.sh in tsan mode on the TSan-built forge
# (TSAN_OPTIONS with log_path + halt_on_error is inherited from run_ci.sh; run_ci.sh fails on any
# report file). Default options: 200 positions x go depth 12 at Threads 2/4/8 and 500 stress
# iterations; then reduced runs with SmpExactNodes + SmpBestThread on.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
FORGE=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
python3 -m pip install --quiet --break-system-packages chess 2>/dev/null || python3 -m pip install --quiet chess || true
status=0
run() { local log=$1; shift; echo "== $*" | tee "$OUT/$log"; "$@" >> "$OUT/$log" 2>&1 || status=1; tail -n 4 "$OUT/$log"; }
run tsan_smp_depth12.log python3 "$HERE/smp_depth.py" "$FORGE" --positions "$ROOT/tools/openings/forge-10000.epd" \
    --count 200 --threads 2,4,8 --depth 12 --timeout 1800
run tsan_uci_stress.log python3 "$HERE/uci_stress.py" "$FORGE" --iterations 500 --seed 20261026 \
    --positions "$ROOT/opus_round1/O3/positions50.fen" --threads 1,2,3,4,8 --slack 120
run tsan_smp_depth12_options_on.log python3 "$HERE/smp_depth.py" "$FORGE" --positions "$ROOT/tools/openings/forge-10000.epd" \
    --count 60 --threads 4,8 --depth 12 --timeout 1800 --option SmpExactNodes=true --option SmpBestThread=true
run tsan_uci_stress_options_toggled.log python3 "$HERE/uci_stress.py" "$FORGE" --iterations 200 --seed 20261027 \
    --positions "$ROOT/opus_round1/O3/positions50.fen" --threads 1,2,4,8 --slack 120 --toggle-options
exit $status
