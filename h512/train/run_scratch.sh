#!/usr/bin/env bash
# run_scratch.sh [max minutes] - JOB E phase 2 (addendum 9): the recipe trained from random initialisation, plan
# h512/train/plans/scratch_wd.json, run folder _work/runs/arms/scratch_wd. No init checkpoint is copied. Restartable.
set -u
maxmin="${1:-115}"
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/arms/scratch_wd"; mkdir -p "$R"
echo "$(date '+%F %T') scratch launcher start pid $$ max minutes $maxmin" >> "$R/queue.log"
"$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/plans/scratch_wd.json" --run-dir "$R" --resume --max-minutes "$maxmin" --log-every 5000 >> "$R/trainer.out" 2>&1
echo "$(date '+%F %T') trainer exit $?" >> "$R/queue.log"
