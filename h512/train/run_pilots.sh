#!/usr/bin/env bash
# JOB E recipe pilots: six arms, one after another on the GPU. Restartable (finished arms are skipped, a stopped arm resumes).
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/pilots"; mkdir -p "$R"
echo "$(date '+%F %T') pilots queue start pid $$" >> "$R/queue.log"
for arm in P0 P1 P2 P3 P4 P5; do
  [ -f "$R/$arm/DONE" ] && continue
  [ -f "$R/STOP_QUEUE" ] && break
  "$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/plans/pilot_$arm.json" --run-dir "$R/$arm" --resume --log-every 5000 >> "$R/$arm.out" 2>&1
  rc=$?; echo "$(date '+%F %T') $arm exit $rc" >> "$R/queue.log"
  if [ $rc -eq 0 ] && grep -q "EXIT plan complete" "$R/$arm/log.txt"; then touch "$R/$arm/DONE"; rm -f "$R/$arm/latest.pt" "$R/$arm/best.pt"; fi
done
echo "$(date '+%F %T') pilots queue finished" >> "$R/queue.log"
