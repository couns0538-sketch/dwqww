#!/bin/bash
# kimi5 job 37 step 4 driver: reads runlist.tsv, runs every row on O and on G at depth 12
# (PC20 + the one option), 4 parallel processes, one engine process per run via runner_j37.py.
# usage: step4_run.sh <engine> <O|G>   (run twice: once O, once G)
set -u
ENGINE="$1"; SET="$2"
J="$(cd "$(dirname "$0")" && pwd)"
W=/tmp/j37
EPD="$W/O.epd"; [ "$SET" = "G" ] && EPD="$W/G.epd"
mkdir -p "$J/s4"
tail -n +2 "$J/runlist.tsv" | while IFS=$'\t' read -r name side value; do
  opt="$J/s4/opt_${name}_${side}.txt"
  grep -v '^#' "$W/pc20.opt" > "$opt"
  echo "$name $value" >> "$opt"
  echo "python3 $J/runner_j37.py $ENGINE $EPD $J/s4 s4_${name}_${side}_$SET go depth 12 -- $opt > $J/s4/s4_${name}_${side}_$SET.log 2>&1"
done | xargs -P4 -I{} sh -c '{}'
echo "step4 $SET done"
