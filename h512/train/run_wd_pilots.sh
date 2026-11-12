#!/usr/bin/env bash
# JOB E phase 2: weight-decay pilot arms, one after another on the GPU, after the main phase-2 run has exited.
# Each arm resumes a copy of the phase-1 state at 1.0B (_work/runs/main/stage_S1.pt) and repeats stage S2 with its own
# plan (h512/train/plans/wd_<arm>.json). Restartable: finished arms are skipped, a stopped arm resumes.
# Usage: run_wd_pilots.sh [arm ...]   (default: W0 W1 W2 W3).  Stop the queue with: touch _work/runs/wd/STOP_QUEUE
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/wd"; mkdir -p "$R"
arms="${*:-W0 W1 W2 W3}"
echo "$(date '+%F %T') wd queue start pid $$ arms: $arms" >> "$R/queue.log"
# wait for the main phase-2 trainer (it owns the GPU until it exits)
while [ ! -f "$R/STOP_QUEUE" ] && ! grep -q "trainer exit" "$D/_work/runs/phase2/queue.log" 2>/dev/null; do sleep 15; done
echo "$(date '+%F %T') main phase-2 trainer has exited; starting arms" >> "$R/queue.log"
for arm in $arms; do
  [ -f "$R/$arm/DONE" ] && continue
  [ -f "$R/STOP_QUEUE" ] && break
  mkdir -p "$R/$arm"
  [ -f "$R/$arm/latest.pt" ] || cp "$D/_work/runs/main/stage_S1.pt" "$R/$arm/latest.pt"
  "$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/plans/wd_$arm.json" --run-dir "$R/$arm" --resume --log-every 5000 >> "$R/$arm.out" 2>&1
  rc=$?; echo "$(date '+%F %T') $arm exit $rc" >> "$R/queue.log"
  if [ $rc -eq 0 ] && grep -q "EXIT plan complete" "$R/$arm/log.txt"; then touch "$R/$arm/DONE"; fi
done
echo "$(date '+%F %T') wd queue finished" >> "$R/queue.log"
