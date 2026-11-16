#!/usr/bin/env bash
# run_pych_ref.sh : 4 parallel python-chess reference workers over R_2301.fens, depth 1..4
set -u
N=$(wc -l < R_2301.fens)
PART=$(( (N + 3) / 4 ))
for k in 0 1 2 3; do
  a=$((k * PART)); b=$(( (k + 1) * PART )); [ $b -gt $N ] && b=$N
  nohup python3 -u pych_worker.py R_2301.fens $a $b 4 pych_R_$k.jsonl > pych_R_$k.log 2>&1 &
done
wait
echo "all workers done"
wc -l pych_R_*.jsonl
