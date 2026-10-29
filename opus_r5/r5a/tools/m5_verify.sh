#!/usr/bin/env bash
# R5A M5 verification in one go (run while smoke_all.sh is paused, so the 3-thread cap holds):
#   1. box build of the worktree head (build_r5a.sh, 3 compiles)    2. lock identity uci_check --full
#   3. option benches: CorrMargins / CorrExt ON at the default scale / threshold must equal the M1 pins; the new
#      spins alone (option OFF) must equal the OFF pins; other values must move the ON trees (the hooks act)
#   4. incremental CMake build (JOBS=3) + CTest list on the 3-CPU mask (run_ctest_3cpu.cmd)
# usage: m5_verify.sh <worktree>      logs: /f/opus_scratch/r5/r5a/logs/*_m5_<head>.*
set -u
WT=$1
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
L=/f/opus_scratch/r5/r5a/logs
H=$(git -C "$WT" rev-parse --short=8 HEAD)
E=/f/opus_scratch/r5/r5a/exe/forge_r5a_m5_$H.exe
cd "$WT"
bash opus_r5/r5a/tools/build_r5a.sh "$WT" "$E" > $L/build_m5_$H.log 2>&1 || { echo "BUILD FAILED"; tail -20 $L/build_m5_$H.log; exit 1; }
tail -2 $L/build_m5_$H.log
echo "warnings: $(grep -ci warning $L/build_m5_$H.log)"
nice -n 10 $PY -I -B $LA/2_build/uci_check.py "$E" --full > $L/identity_m5_$H.log 2>&1
tail -1 $L/identity_m5_$H.log
B=opus_r3/R3-1/tools/bench_opts.py
{
  for spec in "CorrMargins=1" "CorrMargins=1 CorrMarginsScale=100" "CorrMargins=1 CorrMarginsScale=50" \
              "CorrMargins=1 CorrMarginsScale=150" "CorrMarginsScale=150" "CorrMarginsScale=0" \
              "CorrExt=1" "CorrExt=1 CorrExtTripleCorr=48" "CorrExt=1 CorrExtTripleCorr=32" "CorrExtTripleCorr=32"; do
    args=(); for o in $spec; do args+=(--opt "$o"); done
    echo "## $spec"
    nice -n 10 $PY -I -B $B "$E" "${args[@]}" --depths 11,13,16
  done
} > $L/m5_bench_$H.log 2>&1
cat $L/m5_bench_$H.log
JOBS=3 bash /d/grok-pc-data/dwqww/.claude/worktrees/b/tools/cmake_build.sh "$WT" /f/opus_scratch/r5/r5a/cmake/m2 > $L/cmake_m5_$H.log 2>&1 || { echo "CMAKE FAILED"; tail -30 /f/opus_scratch/r5/r5a/cmake/m2.build.log; exit 1; }
echo "cmake warnings in r5a/corr files: $(grep -i warning /f/opus_scratch/r5/r5a/cmake/m2.build.log | grep -ciE 'r5a_options|corr_margins|uci\.cpp|search_tune')"
cmd //c "$(cygpath -w "$WT/opus_r5/r5a/tools/run_ctest_3cpu.cmd")" "$(cygpath -w /f/opus_scratch/r5/r5a/cmake/m2)" "$(cygpath -w $L/ctest_m5_$H.log)"
grep -E "tests passed|tests failed|\(Failed\)|ctest exit" $L/ctest_m5_$H.log
grep -E "forge_r5a_options_tests" $L/ctest_m5_$H.log
echo "exe $E"
