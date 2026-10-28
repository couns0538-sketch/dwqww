#!/usr/bin/env bash
# R3 port C: full CMake build of all targets (JOBS=1, box flags) + full ctest, default configuration.
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
W=/f/opus_scratch/worktrees/opus_r3_port_c
BD=/f/opus_scratch/build/r3_port_c/cmake_default
L=/f/opus_scratch/r3/port_c/logs
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
start=$(date +%s)
JOBS=1 nice -n 19 bash $T/cmake_build.sh "$W" $BD > $L/cmake_default_build_driver.log 2>&1
rc=$?
echo "cmake_build rc=$rc after $(( $(date +%s) - start )) s" >> $L/cmake_default_build_driver.log
cp $BD.build.log $L/cmake_default.build.log 2>/dev/null; cp $BD.configure.log $L/cmake_default.configure.log 2>/dev/null
if [ $rc -ne 0 ]; then echo "BUILD FAILED"; tail -30 $L/cmake_default_build_driver.log; exit 1; fi
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
cd $BD && nice -n 19 ctest --output-on-failure --timeout 600 > $L/ctest_default.log 2>&1
echo "ctest done after $(( $(date +%s) - start )) s" >> $L/cmake_default_build_driver.log
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B $W/opus_round1/ci/check_known_failures.py $L/ctest_default.log > $L/known_failures_default.log 2>&1
echo "known-failure check rc=$?" >> $L/known_failures_default.log
tail -5 $L/ctest_default.log; cat $L/known_failures_default.log
