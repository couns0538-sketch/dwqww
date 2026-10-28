#!/usr/bin/env bash
# R3-6: the measurement matrices (run from anywhere; outputs in $OUT).
#   main  : default (PC recipe) builds. Stack head exe: off / on / on2 at Threads 1,2,3. Fix exe (head +
#           SmpHelpersPastDepth): offP / onP (= off / on + SmpHelpersPastDepth=true) at Threads 2,3
#           (at Threads 1 the option is inert: bench and forge_smp_tests show identical searches).
#   trace : the FORGE_SMP_TRACE build of the fix tree, one repetition: off at Threads 1,2,3, the other
#           configs at Threads 2,3.
# usage: run_matrix.sh main|trace <head_exe> <fix_exe> <trace_exe> <out_dir> [reps]
set -euo pipefail
MODE=$1; B=$2; F=$3; T=$4; OUT=$5; REPS=${6:-3}
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
HERE=$(cd "$(dirname "$0")" && pwd)
ON="SmpExactNodes=true,SmpBestThread=true,LocklessTT=true"
ON2="$ON,CorrHistPlus=7,CorrMargins=1,CorrExt=1,CuckooRep=true,HistRework=2,MaterialKeyTable=true"
if [ "$MODE" = main ]; then
  nice -n 19 "$PY" -I -B "$HERE/smp_ttd.py" --positions "$HERE/positions30.tsv" \
    --config "off=$B" --config "on=$B|$ON" --config "on2=$B|$ON2" \
    --config "offP=$F|SmpHelpersPastDepth=true" --config "onP=$F|$ON,SmpHelpersPastDepth=true" \
    --config-threads offP=2,3 --config-threads onP=2,3 \
    --threads 1,2,3 --reps "$REPS" --hash 64 --out "$OUT/ttd_main.jsonl"
else
  nice -n 19 "$PY" -I -B "$HERE/smp_ttd.py" --positions "$HERE/positions30.tsv" \
    --config "off=$T" --config "on=$T|$ON" --config "on2=$T|$ON2" \
    --config "offP=$T|SmpHelpersPastDepth=true" --config "onP=$T|$ON,SmpHelpersPastDepth=true" \
    --config-threads on=2,3 --config-threads on2=2,3 --config-threads offP=2,3 --config-threads onP=2,3 \
    --threads 1,2,3 --reps 1 --hash 64 --seed 66 --out "$OUT/ttd_trace.jsonl"
fi
