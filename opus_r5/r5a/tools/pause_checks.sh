#!/usr/bin/env bash
# R5A checks run while smoke_all.sh is paused (3 threads at most: two syntax-only compiles + one bench process):
#   1. uci.cpp and search.cpp compile (syntax only, CMake warning flags) with the build switches whose #if blocks
#      the R5A echo touches: FORGE_NNUE_INT16, FORGE_NNUE_LAZY_ACC, FORGE_S13_TT_CHILD_PREFETCH,
#      FORGE_EXPOSE_TUNABLES, FORGE_PROF, FORGE_NNUE_O2 (CI's opus-r3-switches runs only on forge-bundle-*)
#   2. the whole M1 table on the M5 exe must equal the base exe's (logs/m1_bench_base.log)
#   3. forge_r5a_options_tests from the CMake build: PASS / FAIL count
# usage: pause_checks.sh <worktree> <m5 exe> <cmake build dir>
set -u
WT=$1; E=$2; BD=$3
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
L=/f/opus_scratch/r5/r5a/logs
export PATH=/c/msys64/ucrt64/bin:$PATH
cd "$WT"
SW="-DFORGE_NNUE_INT16=1 -DFORGE_NNUE_LAZY_ACC=1 -DFORGE_S13_TT_CHILD_PREFETCH=1 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_PROF=1 -DFORGE_NNUE_O2=1"
FL="-std=c++20 -fsyntax-only -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Iinclude"
nice -n 10 g++ $FL $SW src/uci.cpp > $L/switches_uci_syntax.log 2>&1 &
P1=$!
nice -n 10 g++ $FL $SW src/search.cpp > $L/switches_search_syntax.log 2>&1 &
P2=$!
nice -n 10 $PY -I -B opus_r5/r5a/tools/m1_option_bench.py "$E" --config CorrMargins=1:0 --config CorrExt=1:0 \
  --config CorrHistPlus=2:0 --config CorrHistPlus=4:0 --config CorrHistPlus=6:0 --config NetScale=97:100 \
  --config NetScale=99:100 --config NetScale=101:100 --config NetScale=103:100 --config HistRework=1:0 \
  --config HistRework=3:0 > $L/m1_bench_m5.log 2>&1
wait $P1; R1=$?
wait $P2; R2=$?
echo "switch build syntax: uci.cpp exit $R1 ($(grep -c 'warning' $L/switches_uci_syntax.log) warnings, $(grep -ciE 'r5a|uci\.cpp' $L/switches_uci_syntax.log) lines naming uci.cpp/r5a), search.cpp exit $R2 ($(grep -c 'warning' $L/switches_search_syntax.log) warnings, $(grep -ciE 'r5a_options|corr_margins' $L/switches_search_syntax.log) in r5a/corr_margins)"
if diff <(grep -E '^(OFF|Corr|Net|Hist)' $L/m1_bench_base.log) <(grep -E '^(OFF|Corr|Net|Hist)' $L/m1_bench_m5.log) > /dev/null; then
  echo "M1 table on the M5 exe: IDENTICAL to the base exe ($(tail -1 $L/m1_bench_m5.log))"
else
  echo "M1 table on the M5 exe: DIFFERS"; diff <(grep -E '^(OFF|Corr|Net|Hist)' $L/m1_bench_base.log) <(grep -E '^(OFF|Corr|Net|Hist)' $L/m1_bench_m5.log)
fi
mkdir -p /f/opus_scratch/r5/r5a/tmp/r5a_test_run && cd /f/opus_scratch/r5/r5a/tmp/r5a_test_run
nice -n 10 "$BD/forge_r5a_options_tests.exe" "$BD/forge.exe" > $L/r5a_options_tests_m5.log 2>&1
echo "forge_r5a_options_tests: exit $?, PASS $(grep -c '^PASS' $L/r5a_options_tests_m5.log), FAIL $(grep -c '^FAIL' $L/r5a_options_tests_m5.log), last: $(tail -1 $L/r5a_options_tests_m5.log)"
