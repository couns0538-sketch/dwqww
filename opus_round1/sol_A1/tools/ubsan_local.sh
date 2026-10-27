#!/usr/bin/env bash
# Local UBSan check for HistRework at its maximum (MinGW has no libubsan: trap mode, so any undefined behaviour
# such as signed overflow, an out-of-range shift or a bad enum load executes ud2 and kills the process).
# usage: ubsan_local.sh <src_root> <build_dir> <python_exe> <log_dir>     (run under nice -n 19)
#   1. engine: build_pc.sh + -fsanitize=undefined -fno-sanitize=vptr -fsanitize-undefined-trap-on-error
#   2. uci_check (bench d11/13/16 + perft) with HistRework=0 (must still print ALL OK), then bench d11/d13/d16 at
#      HistRework=3 with HistoryBonusMax/Quadratic/Linear and MaterialCorrectionWeight at their UCI maxima
#      (10000/100/500/300)
#   3. tests/hist_rework_tests.cpp built with the same flags (includes the max-value searches)
set -uo pipefail
SRC=$1; BD=$2; PY=$3; LOG=$4
T=D:/grok-pc-data/dwqww/.claude/worktrees/b/tools
HERE=$(cd "$(dirname "$0")" && pwd)
FLAGS="-fsanitize=undefined -fno-sanitize=vptr -fsanitize-undefined-trap-on-error"
mkdir -p "$BD" "$LOG"
status=0
bash "$T/build_pc.sh" "$SRC" "$BD/forge_a1_ubsan.exe" $FLAGS > "$LOG/ubsan_build_engine.log" 2>&1 || { echo "engine build failed"; tail -20 "$LOG/ubsan_build_engine.log"; exit 1; }
echo "ud2 traps in the engine (UBSan check sites): $(/c/msys64/ucrt64/bin/objdump.exe -d "$BD/forge_a1_ubsan.exe" | grep -c 'ud2')" | tee -a "$LOG/ubsan_build_engine.log"
"$PY" -I -B D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039/2_build/uci_check.py \
  "$BD/forge_a1_ubsan.exe" > "$LOG/ubsan_uci_check_off.log" 2>&1 || status=1
"$PY" -I -B "$HERE/bench_sweep.py" "$BD/forge_a1_ubsan.exe" --values 3 --depths 11 13 16 \
  --set HistoryBonusMax=10000 HistoryBonusQuadratic=100 HistoryBonusLinear=500 MaterialCorrectionWeight=300 \
  > "$LOG/ubsan_bench_max.log" 2>&1 || status=1
bash "$HERE/build_test.sh" "$SRC" "$BD/hist_rework_tests_ubsan.exe" $FLAGS > "$LOG/ubsan_build_test.log" 2>&1 || { echo "test build failed"; exit 1; }
"$BD/hist_rework_tests_ubsan.exe" > "$LOG/ubsan_hist_rework_tests.log" 2>&1
rc=$?
echo "hist_rework_tests (UBSan trap build) exit $rc" | tee -a "$LOG/ubsan_hist_rework_tests.log"
[ "$rc" -eq 0 ] || status=1
echo "ubsan_local status=$status"
exit $status
