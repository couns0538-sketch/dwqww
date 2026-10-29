#!/usr/bin/env bash
# R6 J4: single-thread loader throughput, alternating builds (ABAB...) on the loaded PC.
# usage: bench_loader.sh ITERS ROUNDS dir1 dir2 ...   (each dir has training_data_loader_bench.exe + DLL)
iters=$1; rounds=$2; shift 2
export PATH="/c/msys64/ucrt64/bin:$PATH"
IN=F:/opus_scratch/r6/nnue-pytorch-amd/.pgo/small.binpack
for r in $(seq 1 "$rounds"); do
  for d in "$@"; do
    ( cd "$d" && nice -n 10 ./training_data_loader_bench.exe -i "$iters" -p 1 -c 0 "$IN" 2>&1 ) \
      | tr '\r' '\n' | grep -a "Iter:" | tail -1 \
      | awk -v d="$(basename "$d")" -v r="$r" '{print "round " r " " d ": " $0}'
  done
done
