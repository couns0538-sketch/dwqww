#!/bin/bash
# kimi5 job 20 Step 2: the five settings of Step 1 at depth 14, O and G.
# usage: step2_batch.sh <engine> <rowsdir>
set -u
EXE="$1"; ROWS="$2"; mkdir -p "$ROWS"
JOB="$(cd "$(dirname "$0")" && pwd)"

date -u > "$ROWS/step2_batch.start"
for s in base cfb230 snd32 gcd32 all3; do
  echo "$s O"
  echo "$s G"
done | xargs -d '\n' -n 1 -P 4 bash -c '
  line="$1"; set -- $line
  python3 "'"$JOB"'/runner_j20.py" "'"$EXE"'" "'"$JOB"'/$2.epd" 14 "'"$ROWS"'" "$1_$2_d14" 1000000 1 "'"$JOB"'/$1.opt" > "'"$ROWS"'/$1_$2_d14.runlog" 2>&1
' _
date -u > "$ROWS/step2_batch.end"
grep -h "^DONE" "$ROWS"/*_d14.runlog
