#!/usr/bin/env bash
# JOB E follow-up (phase 2): continue the staged run from the end of stage S2 toward 7.4B presentations, in its own
# run folder so that the phase-1 run folder (_work/runs/main, hashes in results/step6/main_files.md5) stays as it is.
# Restartable: a stopped run resumes from latest.pt. Stop cleanly with:  touch _work/runs/phase2/STOP
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/phase2"; mkdir -p "$R"; rm -f "$R/STOP"
if [ ! -f "$R/latest.pt" ]; then
  cp "$D/_work/runs/main/latest.pt" "$R/latest.pt"
  echo "$(date '+%F %T') copied runs/main/latest.pt md5 $(md5sum "$R/latest.pt" | cut -c1-32)" >> "$R/queue.log"
fi
echo "$(date '+%F %T') phase-2 launcher start pid $$" >> "$R/queue.log"
"$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/phase2_config.json" --run-dir "$R" --resume \
  --clear-stop "owner asked on 2026-11-11 to use the remaining allowance; brief target 7.4B" --max-minutes 105 \
  --log-every 5000 >> "$R/trainer.out" 2>&1
echo "$(date '+%F %T') trainer exit $?" >> "$R/queue.log"
