#!/usr/bin/env bash
# R3-4: full local CMake build (all targets, JOBS=1) + full ctest + known-failure check, on the PC.
# usage: run_cmake_ctest.sh <src worktree> <build dir> <log prefix>
set -uo pipefail
SRC=$1; BD=$2; LOG=$3
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
echo "== $(date -u +%FT%TZ) head $(git -C "$SRC" rev-parse HEAD) dirty files: $(git -C "$SRC" status --porcelain | wc -l)" > "$LOG.summary"
start=$(date +%s)
JOBS=1 nice -n 19 bash /d/grok-pc-data/dwqww/.claude/worktrees/b/tools/cmake_build.sh "$SRC" "$BD" > "$LOG.build.log" 2>&1
rc=$?
echo "== cmake build rc=$rc ($(( $(date +%s) - start )) s)" >> "$LOG.summary"
[ $rc -eq 0 ] || exit $rc
start=$(date +%s)
(cd "$BD" && nice -n 19 ctest --output-on-failure --timeout 600) > "$LOG.ctest.log" 2>&1
echo "== ctest rc=$? ($(( $(date +%s) - start )) s)" >> "$LOG.summary"
grep -E "tests passed|opus_spsa" "$LOG.ctest.log" >> "$LOG.summary"
C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B "$SRC/opus_round1/ci/check_known_failures.py" "$LOG.ctest.log" >> "$LOG.summary" 2>&1
echo "== known-failure check rc=$?" >> "$LOG.summary"
