#!/usr/bin/env bash
# port_b step 3b: forge_smp_tests failed once in the FORGE_ATTACKS_INIT_ONCE=ON CMake build (SmpExactNodes overshoot
# bound: nodes < 20000 + 3 threads x 2100, got 26333 and 27724) while it passed in the default and FORGE_DATAGEN=ON
# builds. Load or switch? Run the same test binary from the default build and from the ON build alternately, same
# conditions (nice 19, loaded PC), N rounds each, and count failures per build.
set -u
B=/f/opus_scratch/build/r3_port_b
L=/f/opus_scratch/r3/port_b
N=${1:-8}
export PATH=/c/msys64/ucrt64/bin:$PATH
fail_default=0; fail_on=0
for i in $(seq 1 $N); do
  for cfg in cmake cmake_initonce; do
    out=$(cd $B/$cfg && nice -n 19 ./forge_smp_tests.exe 2>&1); rc=$?
    echo "round $i $cfg rc=$rc :: $(echo "$out" | grep -E '^FAIL|housekeeping' | tr '\n' ' ')"
    if [ $rc -ne 0 ]; then
      if [ $cfg = cmake ]; then fail_default=$((fail_default+1)); else fail_on=$((fail_on+1)); fi
    fi
  done
done
echo "SUMMARY forge_smp_tests failures: default build $fail_default/$N, FORGE_ATTACKS_INIT_ONCE=ON build $fail_on/$N"
