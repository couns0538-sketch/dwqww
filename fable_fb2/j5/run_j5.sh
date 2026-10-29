#!/usr/bin/env bash
# FB2-J5 verification + measurement. usage: run_j5.sh <phase>
#   tests   : unit tests (3 threads for seconds) + full ctest (except forge_tests) + box build + OFF identity
#   ttd12   : time-to-depth, threads 1 and 2, off vs SmpV2 (30 positions, 1 repetition)     [2 threads]
#   ttd3    : time-to-depth, threads 3, off vs SmpV2                                        [3 threads: training paused]
set -uo pipefail
PHASE=$1
WT=/f/opus_scratch/worktrees/fable_fb2_j5
T=D:/grok-pc-data/dwqww/.claude/worktrees/b/tools
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
L=/f/opus_scratch/fable/fb2/j5
BD=/f/opus_scratch/build/fable_fb2/j5_cmake
EXE=/f/opus_scratch/build/fable_fb2/forge_fable_j5.exe
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
cd "$WT"
case "$PHASE" in
  tests)
    nice -n 19 "$BD/forge_fb2_j5_tests.exe" > "$L/unit_tests.log" 2>&1; echo "unit exit $?" >> "$L/unit_tests.log"
    (cd "$BD" && nice -n 19 ctest -E '^forge_tests$' --output-on-failure --timeout 1200 > "$L/ctest_j5.log" 2>&1; echo "ctest exit $?" >> "$L/ctest_j5.log")
    FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp" nice -n 19 bash $T/build_pc.sh "$PWD" "$EXE" > "$L/build_pc_j5.log" 2>&1
    echo "build exit $?" >> "$L/build_pc_j5.log"; echo "warnings $(grep -ci warning "$L/build_pc_j5.log")" >> "$L/build_pc_j5.log"
    nice -n 19 $PY -I -B $LA/2_build/uci_check.py "$EXE" --full > "$L/identity_off_j5.log" 2>&1; echo "identity exit $?" >> "$L/identity_off_j5.log"
    echo "tests done" >> "$L/identity_off_j5.log"
    ;;
  ttd12)
    nice -n 19 $PY -I -B tools/smp/fable_smp_ttd.py "$EXE" "$L/tools/positions30.tsv" --threads 1,2 --configs "off:,on:SmpV2=true" --reps 1 --out "$L/smp_ttd_t12.csv" > "$L/smp_ttd_t12.log" 2>&1
    echo "ttd12 exit $?" >> "$L/smp_ttd_t12.log"
    ;;
  ttd3)
    nice -n 19 $PY -I -B tools/smp/fable_smp_ttd.py "$EXE" "$L/tools/positions30.tsv" --threads 1,3 --configs "off:,on:SmpV2=true" --reps 1 --out "$L/smp_ttd_t3.csv" > "$L/smp_ttd_t3.log" 2>&1
    echo "ttd3 exit $?" >> "$L/smp_ttd_t3.log"
    ;;
esac
