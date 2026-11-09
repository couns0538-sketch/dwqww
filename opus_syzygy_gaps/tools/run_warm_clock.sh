#!/usr/bin/env bash
# run_warm_clock.sh <exe name in out/exe> <out name> [--opt N=V ...] - warm clock fixture, decided rows, 3-4 piece tables, depth 14.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
exe=$1; name=$2
shift 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe 'C:\Python315\python.exe' \
  -ArgLine "-I -B $W\\repo\\opus_syzygy_gaps\\tools\\warm_claims.py clock $W\\out\\exe\\${exe}.exe $W\\out\\exp\\warm\\${WARM_IN:-f1.clock_decided.tsv} $W\\out\\exp\\warm\\${name}.jsonl --tables $W\\out\\tb\\man34 --depth ${WARM_DEPTH:-14} --jobs ${WARM_JOBS:-3} $*" \
  -Log "$W\\out\\exp\\warm\\${name}.log"
echo "== $name $*"
cut -c1-200 "$J/out/exp/warm/${name}.log" | head -9
