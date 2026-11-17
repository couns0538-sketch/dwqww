#!/bin/bash
# kimi5 job 20 Step 4 (owed from job 17): the LmrFine port in states that CHANGE the tree.
# Build: 6b98f217 + pc_r15 + LmrFine.pc.patch.txt (sha256 986c10e4...), S14, depth 12.
# usage: step4_run.sh <lmrfine_engine>
set -u
EXE="$1"
JOB="$(cd "$(dirname "$0")" && pwd)"
ROWS="$JOB/rows_lmr"
mkdir -p "$ROWS"

date -u > "$ROWS/step4.start"
python3 "$JOB/runner_j20.py" "$EXE" "$JOB/O.epd" 12 "$ROWS" t1_O_d12 1000000 1 "$JOB/t1.opt" > "$ROWS/t1_O.runlog" 2>&1 &
python3 "$JOB/runner_j20.py" "$EXE" "$JOB/G.epd" 12 "$ROWS" t1_G_d12 1000000 1 "$JOB/t1.opt" > "$ROWS/t1_G.runlog" 2>&1 &
python3 "$JOB/runner_j20.py" "$EXE" "$JOB/O.epd" 12 "$ROWS" c1_O_d12 1000000 1 "$JOB/c1.opt" > "$ROWS/c1_O.runlog" 2>&1 &
wait
date -u > "$ROWS/step4.end"
grep -h "^DONE" "$ROWS"/*.runlog
