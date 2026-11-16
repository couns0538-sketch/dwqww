#!/usr/bin/env bash
# wait for the 200-position R reference to finish, then run the 30 G positions over 4 workers
while pgrep -f "pych_worker.py R200" > /dev/null; do sleep 10; done
echo "R200 reference processes gone at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 -u pych_worker.py G30.fens 0 8 5 pych_G30_0.jsonl > pych_G30_0.log 2>&1 &
python3 -u pych_worker.py G30.fens 8 15 5 pych_G30_1.jsonl > pych_G30_1.log 2>&1 &
python3 -u pych_worker.py G30.fens 15 22 5 pych_G30_2.jsonl > pych_G30_2.log 2>&1 &
python3 -u pych_worker.py G30.fens 22 30 5 pych_G30_3.jsonl > pych_G30_3.log 2>&1 &
wait
echo "G30 done at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
