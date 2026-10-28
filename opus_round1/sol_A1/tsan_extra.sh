#!/usr/bin/env bash
# CI TSan hook (opus_round1/ci/run_ci.sh tsan): HistRework 0 and 3 with Threads 1 and 4 on the TSan engine.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
EXE=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd)
echo "== sol_A1 tsan_extra: smp_smoke HistRework 0/3, Threads 1/1/4, depth 8"
python3 "$HERE/tools/smp_smoke.py" "$EXE" 8 1,1,4 2>&1 | tee "$OUT/sol_A1_smp_smoke_tsan.log"
exit "${PIPESTATUS[0]}"
