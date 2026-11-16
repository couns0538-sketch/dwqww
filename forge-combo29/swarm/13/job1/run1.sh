#!/usr/bin/env bash
# area 3 job 1 full run: perft 1..4 on 5000 R positions, engine and reference in parallel
set -u
cd "$(dirname "$0")"
date -u >> stamps.txt
python3 engine_perft.py /home/ubuntu/b/rel/forge R_1301.fens raw_engine.txt 1,2,3,4 120 > engine.log 2>&1 &
EP=$!
python3 ref_perft.py R_1301.fens raw_ref.txt 1,2,3,4 > ref.log 2>&1 &
RP=$!
wait $EP; echo "engine_exit=$?" >> run1.status
wait $RP; echo "ref_exit=$?" >> run1.status
date -u >> stamps.txt
echo RUNDONE >> run1.status
