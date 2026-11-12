#!/usr/bin/env bash
# JOB E staged training run from h512/train/stage1_config.json. Restartable: a stopped run resumes from latest.pt
# with the same data position. Stop cleanly with:  touch _work/runs/main/STOP
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/main"; mkdir -p "$R"; rm -f "$R/STOP"
echo "$(date '+%F %T') main run launcher start pid $$" >> "$R/queue.log"
"$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/stage1_config.json" --run-dir "$R" --resume --log-every 5000 >> "$R/trainer.out" 2>&1
echo "$(date '+%F %T') trainer exit $?" >> "$R/queue.log"
