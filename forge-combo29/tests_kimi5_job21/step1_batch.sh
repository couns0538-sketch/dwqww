#!/bin/bash
# kimi5 job 21 Step 1: known-answer rows at depth 12, PC20, O (200) and G (353).
# usage: step1_batch.sh <engine> <rowsdir>
set -u
EXE="$1"; ROWS="$2"; mkdir -p "$ROWS"
JOB="$(cd "$(dirname "$0")" && pwd)"

date -u > "$ROWS/step1_batch.start"
for s in base lmr2048 lmr8192 cap4 lmr0 all3; do
  echo "$s O"
  echo "$s G"
done | xargs -d '\n' -n 1 -P 4 bash -c '
  line="$1"; set -- $line
  python3 "'"$JOB"'/runner_j20.py" "'"$EXE"'" "'"$JOB"'/$2.epd" 12 "'"$ROWS"'" "$1_$2_d12" 1000000 1 "'"$JOB"'/$1.opt" > "'"$ROWS"'/$1_$2_d12.runlog" 2>&1
' _
date -u > "$ROWS/step1_batch.end"
grep -h "^DONE" "$ROWS"/*.runlog
