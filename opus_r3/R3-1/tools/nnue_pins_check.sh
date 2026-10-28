#!/bin/bash
# Recorded NNUE ON pins of the branches (trained smoke nets) re-run on a stack exe.
EXE=${1:-/f/opus_scratch/build/r3/m_s08.exe}
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
B=F:/opus_scratch/r3/tools/bench_opts.py
run() { # name, expected, opts...
  local name=$1 exp=$2; shift 2
  local got
  got=$(nice -n 19 $PY -I -B $B "$EXE" "$@" --depths 11,13,16,20 2>&1 | awk '/^bench/{printf "%s ", $4} /ERROR/{print "ERR:" $0}')
  got=${got% }
  if [ "$got" = "$exp" ]; then echo "OK    $name: $got"; else echo "DIFF  $name: got [$got] expected [$exp]"; fi
}
run "C5 smoke ob8 (NNUEOutputBuckets 8)" "347579 1100105 2902266 14958675" \
  --opt NNUEFile=F:/opus_scratch/c5/smoke_ob8/epoch003-step000000585.fnn2 --opt NNUEOutputBuckets=8
run "C5 smoke kb4+ob8 (NNUEKingBuckets 4, NNUEOutputBuckets 8)" "544057 1266127 3882123 17316510" \
  --opt NNUEFile=F:/opus_scratch/c5/smoke_kb4ob8/epoch003-step000000585.fnn2 --opt NNUEKingBuckets=4 --opt NNUEOutputBuckets=8
run "O6 threat net (NNUEThreats 1)" "343217 1069707 3461769 10485984" \
  --opt NNUEFile=F:/opus_scratch/o6/r1/o6_cpu_threats/epoch002-step000000160.fnn2 --opt NNUEThreats=1
run "O7 pawn-pair net (NNUEPawnPairs 1)" "325381 803697 3053216 13860219" \
  --opt NNUEFile=F:/opus_scratch/o7/r1/o7_cpu_pawns/epoch002-step000000200.fnn2 --opt NNUEPawnPairs=1
run "O4 pure material net (PureNnue 1)" "450072 1280779 5669969 27276967" \
  --opt NNUEFile=F:/opus_scratch/o4/r2/o4_cpu_material/epoch004-step000000780.fnn2 --opt PureNnue=1
