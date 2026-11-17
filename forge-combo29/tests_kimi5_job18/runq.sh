#!/bin/bash
# kimi5 job 18: Step 1 + Step 2 measurement queue. One engine process per run
# (runner_j18.py; ucinewgame + isready before every search; refusal = stop).
set -u
EXE=${EXE:-/tmp/j18/build/forge}
cd "$(dirname "$0")"
run() { # $1 set (O|G), $2 setting (arr0|arr1|arr2|arr2m16), $3 depth
  python3 runner_j18.py "$EXE" "$1.epd" "$3" rows "$1_$2_d$3" 100000 1 "$2.opt" \
    > "rows/$1_$2_d$3.stdout" 2>&1
  echo "$1_$2_d$3 rc=$?"
}
for s in O G; do
  for d in 12 14 16; do
    for a in arr0 arr1 arr2 arr2m16; do
      run "$s" "$a" "$d"
    done
  done
done
echo QUEUE_DONE
