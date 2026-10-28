#!/bin/bash
# Build the stack worktree with the PC recipe and run the quick identity check (bench d11/13/16 + perft).
# usage: quick_check.sh <name> [extra g++ flags...]   -> /f/opus_scratch/build/r3/<name>.exe, logs in r3/logs
set -u
NAME=$1; shift
WT=/f/opus_scratch/worktrees/opus_r3_stack
OUT=/f/opus_scratch/build/r3/$NAME.exe
LOG=/f/opus_scratch/r3/logs
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
nice -n 19 bash /d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh "$WT" "$OUT" "$@" > $LOG/build_$NAME.log 2>&1
rc=$?
tail -2 $LOG/build_$NAME.log
echo "warnings: $(grep -ci warning $LOG/build_$NAME.log)"
[ $rc -ne 0 ] && { echo "BUILD FAILED"; grep -m 20 -E 'error' $LOG/build_$NAME.log; exit 1; }
nice -n 19 $PY -I -B $LA/2_build/uci_check.py "$OUT" ${FULL:+--full} > $LOG/identity_$NAME.log 2>&1
tail -1 $LOG/identity_$NAME.log
