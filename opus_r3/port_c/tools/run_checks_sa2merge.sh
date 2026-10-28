#!/usr/bin/env bash
# R3 port C: identity + NnueInt16 ON checks of the SA2-merge PC builds (nice 19, one process at a time).
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
B=F:/opus_scratch/build/r3_port_c
L=F:/opus_scratch/r3/port_c/logs
nice -n 19 $PY -I -B $LA/2_build/uci_check.py $B/sa2merge_default.exe --full > $L/uci_check_full_sa2merge_default.log 2>&1
nice -n 19 $PY -I -B $LA/2_build/uci_check.py $B/sa2merge_int16.exe --full > $L/uci_check_full_sa2merge_int16_off.log 2>&1
nice -n 19 $PY -I -B F:/opus_scratch/r3/tools/bench_opts.py $B/sa2merge_int16.exe --opt NnueInt16=true --depths 11,13,16,20,22 --json $L/bench_sa2merge_int16_on.json > $L/bench_sa2merge_int16_on.log 2>&1
echo done
