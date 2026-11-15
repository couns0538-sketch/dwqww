#!/bin/bash
BASE=/tmp/baseline_src/build/forge
PAT=/tmp/patched_src/build/forge
B1="setoption name BundlePreset value B1"
HR2="setoption name HistRework value 2"
python3 /tmp/run_bench.py 2 20 /tmp/results/m1.txt "baseA:$BASE:$B1" "baseB:$BASE:$B1"
python3 /tmp/run_bench.py 2 20 /tmp/results/m2_b1.txt "base:$BASE:$B1" "patched:$PAT:$B1"
python3 /tmp/run_bench.py 2 20 /tmp/results/m2_hr2.txt "base:$BASE:$HR2" "patched:$PAT:$HR2"
python3 /tmp/run_bench.py 2 20 /tmp/results/m2_noopt.txt "base:$BASE:" "patched:$PAT:"
python3 /tmp/run_bench.py 2 20 /tmp/results/m3_base.txt "hr2:$BASE:$HR2" "noopt:$BASE:"
python3 /tmp/run_bench.py 2 20 /tmp/results/m3_patched.txt "hr2:$PAT:$HR2" "noopt:$PAT:"
echo ALL_M_DONE
