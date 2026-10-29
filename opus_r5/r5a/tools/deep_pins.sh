#!/usr/bin/env bash
# R5A M4 extra: d20/d22 ON pins for the 8 gate entries on one exe (the R3 queue's prebench depths are 11/13/16/20/22),
# 3 bench processes at once (BelowNormal), run while smoke_all.sh is paused. One log per config + a summary table.
# usage: deep_pins.sh <exe> <out dir>
set -u
E=$1; OUT=$2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
WT=$(cd "$(dirname "$0")/../../.." && pwd)
mkdir -p "$OUT"
printf '%s\n' CorrHistPlus=4 CorrExt=1 CorrMargins=1 CorrHistPlus=2 CorrHistPlus=6 NetScale=99 HistRework=3 HistRework=1 |
  nice -n 10 xargs -P 3 -I{} sh -c "$PY -I -B $WT/opus_r3/R3-1/tools/bench_opts.py $E --opt {} --depths 20,22 > $OUT/deep_{}.log 2>&1"
for c in CorrHistPlus=4 CorrExt=1 CorrMargins=1 CorrHistPlus=2 CorrHistPlus=6 NetScale=99 HistRework=3 HistRework=1; do
  echo "$c $(grep -o 'd20 nodes [0-9]*' $OUT/deep_$c.log | cut -d' ' -f3) $(grep -o 'd22 nodes [0-9]*' $OUT/deep_$c.log | cut -d' ' -f3)"
done | tee $OUT/deep_pins.txt
