#!/bin/bash
# Run the full ctest list like opus_round1/ci/run_ci.sh (release) and the known-failure check.
BD=$1; OUT=$2
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
cd "$BD" && nice -n 19 ctest --output-on-failure --timeout 600 > "$OUT" 2>&1
echo "ctest exit $?" >> "$OUT"
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B /f/opus_scratch/worktrees/opus_r3_stack/opus_round1/ci/check_known_failures.py "$OUT" >> "$OUT.known" 2>&1
echo "known-check exit $?" >> "$OUT.known"
