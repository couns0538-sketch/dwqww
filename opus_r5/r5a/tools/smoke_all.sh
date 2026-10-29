#!/usr/bin/env bash
# R5A M3 driver: smoke.py for each option config in turn (200 games 5+0.05, 3 games at once, BelowNormal, plus the
# 50x go/stop stress), results into opus_r5/r5a/smoke/<name>/. Cooperative control files in $SCR:
#   PAUSE      -> wait before starting the next config (lets a build run inside the 3-thread budget)
#   STOP_ALL   -> start no further config (smoke.py itself stops between games on <out>/STOP)
# usage: smoke_all.sh <exe> <worktree> [name=Opt:Value[,Opt:Value] ...]
set -u
EXE=$1; WT=$2; shift 2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SCR=/f/opus_scratch/r5/r5a/smoke_ctl
mkdir -p "$SCR"
seed=101
for spec in "$@"; do
  name=${spec%%=*}; opts=${spec#*=}
  while [ -f "$SCR/PAUSE" ]; do sleep 10; done
  [ -f "$SCR/STOP_ALL" ] && { echo "STOP_ALL: not starting $name"; break; }
  args=()
  IFS=',' read -ra kv <<< "$opts"
  for o in "${kv[@]}"; do args+=(--opt "${o%%:*}=${o#*:}"); done
  echo "=== $name (${args[*]}) seed $seed"
  nice -n 10 "$PY" -I -B "$WT/opus_r5/r5a/smoke.py" "$EXE" --name "$name" "${args[@]}" \
      --out "$WT/opus_r5/r5a/smoke/$name" --seed $seed --games 200 --tc 5+0.05 --concurrency 3
  echo "=== $name exit $?"
  seed=$((seed + 100))
done
echo "=== smoke_all done"
