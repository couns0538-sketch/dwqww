#!/usr/bin/env bash
# run_h1024.sh [max minutes] - wider-net pilot (2026-11-12): plan h512/train/plans/h1024_pilot.json, run folder
# _work/runs/arms/h1024_pilot. Random initialisation, 1024 hidden units, otherwise the scratch_wd recipe. Restartable.
# Stop cleanly with: touch _work/runs/arms/h1024_pilot/STOP
set -u
maxmin="${1:-200}"
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/arms/h1024_pilot"; mkdir -p "$R"
echo "$(date '+%F %T') h1024 launcher start pid $$ max minutes $maxmin" >> "$R/queue.log"
"$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/plans/h1024_pilot.json" --run-dir "$R" --resume --max-minutes "$maxmin" --log-every 5000 >> "$R/trainer.out" 2>&1
echo "$(date '+%F %T') trainer exit $?" >> "$R/queue.log"
