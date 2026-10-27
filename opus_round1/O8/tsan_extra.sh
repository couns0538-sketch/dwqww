#!/usr/bin/env bash
# O8 TSan hook (opus_round1/ci/run_ci.sh, tsan job): UCI CorrExt 1 with Lazy SMP helpers.
# The CorrExt search instance adds no shared state (option and weights are read-only during a search;
# the per-path budget lives in each worker's own search stack); this runs it at Threads 2 and 4 under
# TSan, 4 positions, depth 8, each run time-limited.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
EXE=$1
OUT=$2
DIR=$(cd "$(dirname "$0")" && pwd)
echo "== O8 tsan_extra: smp_smoke CorrExt=1 Threads 2,4 depth 8"
timeout --kill-after=10 600 python3 "$DIR/smp_smoke.py" "$EXE" 8 2,4 CorrExt=1 2>&1 | tee "$OUT/tsan_o8_corr_ext_smp.log"
rc=${PIPESTATUS[0]}
echo "== O8 tsan_extra exit $rc"
exit "$rc"
