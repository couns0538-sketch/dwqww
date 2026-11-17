#!/bin/bash
# kimi5 job 20 Step 3: counting build, base / snd32 / gcd32, O and G, depth 12.
# usage: step3_batch.sh <counting_engine> <rowsdir>
set -u
EXE="$1"; ROWS="$2"; mkdir -p "$ROWS"
JOB="$(cd "$(dirname "$0")" && pwd)"

date -u > "$ROWS/step3_batch.start"
for s in base snd32 gcd32; do
  echo "$s O"
  echo "$s G"
done | xargs -d '\n' -n 1 -P 4 bash -c '
  line="$1"; set -- $line
  python3 "'"$JOB"'/runner_j20.py" "'"$EXE"'" "'"$JOB"'/$2.epd" 12 "'"$ROWS"'" "c$1_$2_d12" 1000000 1 "'"$JOB"'/$1.opt" > "'"$ROWS"'/c$1_$2_d12.runlog" 2>&1
' _
date -u > "$ROWS/step3_batch.end"
grep -h "^DONE" "$ROWS"/c*_d12.runlog
