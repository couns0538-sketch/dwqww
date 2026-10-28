#!/usr/bin/env bash
# R3 port C: identity / NnueInt16 ON / UCI regression / v2 non-interference checks of the final-head PC builds
# (nice 19, one engine process at a time).
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
B=F:/opus_scratch/build/r3_port_c
L=F:/opus_scratch/r3/port_c/logs
W=F:/opus_scratch/worktrees/opus_r3_port_c
N=F:/opus_scratch/r3/port_c/nets
for x in final_default final_o2 final_int16 final_int16_o2; do
  nice -n 19 $PY -I -B $LA/2_build/uci_check.py $B/$x.exe --full > $L/uci_check_full_$x.log 2>&1
done
for x in final_int16 final_int16_o2; do
  nice -n 19 $PY -I -B $W/opus_r3/port_c/bench_expect.py $B/$x.exe --opt NnueInt16=true --expect 11=330610,13=858175,16=2760596,20=9564588,22=21638970 --need "NnueInt16 active" > $L/bench_on_$x.log 2>&1
  nice -n 19 $PY -I -B $W/tools/nnue_int16_regression.py $B/$x.exe > $L/nnue_int16_regression_$x.log 2>&1
  # v2 non-interference: a lock replica (v2 path) with NnueInt16 on must search the lock tree (v2 nets stay float).
  nice -n 19 $PY -I -B $W/opus_r3/port_c/bench_expect.py $B/$x.exe --opt NNUEFile=$N/lock_h256_r1.fnn2 --opt NNUEKingBuckets=1 --opt NnueInt16=true --expect 11=312866,13=862329,16=3024920 --need "NNUE v2: active" --need "NnueInt16 active" > $L/bench_v2replica_int16on_$x.log 2>&1
done
nice -n 19 $PY -I -B $W/tools/nnue_int16_regression.py --absent $B/final_default.exe > $L/nnue_int16_regression_absent_final_default.log 2>&1
nice -n 19 $PY -I -B $W/tools/nnue_int16_regression.py --absent $B/final_o2.exe > $L/nnue_int16_regression_absent_final_o2.log 2>&1
echo checks done
