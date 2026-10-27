#!/usr/bin/env bash
# C6 TSan run, called by opus_round1/ci/run_ci.sh in tsan mode on the TSan-built forge (TSAN_OPTIONS
# with log_path + halt_on_error is inherited; run_ci.sh fails on any report file).
# C6 adds no threading; this exercises UCI CuckooRep with helper threads (Threads 2 and 4, depth 8,
# 16 searches, the option toggled between searches). Short by design: one test, hard cap below,
# printed before it starts and on timeout; the engine runs under `nice -n 5`.
# usage: tsan_extra.sh <forge_exe> <out_dir>
set -uo pipefail
FORGE=$1; OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd)
status=0
name=cuckoo_smp_t2_t4_depth8
limit=300
echo "== [C6 tsan] $(date +%T) start $name (timeout ${limit}s)"
timeout --kill-after=10 "$limit" nice -n 5 python3 -u "$HERE/cuckoo_smp.py" "$FORGE" --threads 2,4 --depth 8 \
  --timeout 120 > "$OUT/tsan_c6_$name.log" 2>&1
rc=$?
if [ $rc -eq 124 ] || [ $rc -eq 137 ]; then
  echo "== [C6 tsan] TIMEOUT in $name after ${limit}s - last output:"; tail -n 20 "$OUT/tsan_c6_$name.log"; status=1
elif [ $rc -ne 0 ]; then
  echo "== [C6 tsan] FAIL $name (exit $rc):"; tail -n 20 "$OUT/tsan_c6_$name.log"; status=1
else
  echo "== [C6 tsan] $(date +%T) PASS $name"; tail -n 3 "$OUT/tsan_c6_$name.log"
fi
exit $status
