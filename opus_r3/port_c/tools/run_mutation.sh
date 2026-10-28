#!/usr/bin/env bash
# R3 port C planted-bug check in both FORGE_NNUE_O2 states (one g++ / one test process at a time, Idle priority).
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
W=F:/opus_scratch/worktrees/opus_r3_port_c
S=/f/opus_scratch/r3/port_c
nice -n 19 $PY -I -B $W/opus_r3/port_c/mutation_check_port_c.py $W F:/opus_scratch/r3/port_c/mutants_o2off > $S/logs/mutation_port_c_o2off.log 2>&1
cp $S/mutants_o2off/mutation_result.json $S/logs/mutation_port_c_o2off.json
nice -n 19 $PY -I -B $W/opus_r3/port_c/mutation_check_port_c.py $W F:/opus_scratch/r3/port_c/mutants_o2on --o2 > $S/logs/mutation_port_c_o2on.log 2>&1
cp $S/mutants_o2on/mutation_result.json $S/logs/mutation_port_c_o2on.json
cat $S/logs/mutation_port_c_o2off.log $S/logs/mutation_port_c_o2on.log
