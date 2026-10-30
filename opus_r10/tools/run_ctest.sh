#!/bin/bash
# R9: CMake build of ALL targets (JOBS, default 1) + the full ctest list + the known-failure check, like
# opus_round1/ci/run_ci.sh (release). usage: run_ctest_r9.sh <src_dir> <build_dir> <ctest_log>
# Run it under a CPU mask: python -I -B run_pinned.py --mask 0x000F -- bash_run.py run_ctest_r9.sh ...
SRC=$1; BD=$2; OUT=$3
T=D:/grok-pc-data/dwqww/.claude/worktrees/b/tools
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
JOBS=${JOBS:-1} bash "$T/cmake_build.sh" "$SRC" "$BD" || { echo "cmake build FAILED"; exit 1; }
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
cd "$BD" && nice -n 10 ctest --output-on-failure --timeout 900 > "$OUT" 2>&1
echo "ctest exit $?" >> "$OUT"
"$PY" -I -B "$SRC/opus_round1/ci/check_known_failures.py" "$OUT" > "$OUT.known" 2>&1
echo "known-check exit $?" >> "$OUT.known"
tail -3 "$OUT"; cat "$OUT.known"
