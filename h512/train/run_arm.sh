#!/usr/bin/env bash
# run_arm.sh <arm name> <init checkpoint (.pt of this job)> [extra trainer arguments]
# JOB E phase 2: one training arm in its own run folder _work/runs/arms/<arm>, plan h512/train/plans/<arm>.json.
# The arm resumes a copy of the given checkpoint (model, Adam, RNG, data position). Restartable.
set -u
arm="$1"; init="$2"; shift 2
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
R="$D/_work/runs/arms/$arm"; mkdir -p "$R"
[ -f "$R/DONE" ] && { echo "$arm already done"; exit 0; }
if [ ! -f "$R/latest.pt" ]; then
  cp "$init" "$R/latest.pt"
  echo "$(date '+%F %T') init copied from $init md5 $(md5sum "$R/latest.pt" | cut -c1-32)" >> "$R/queue.log"
fi
echo "$(date '+%F %T') arm $arm launcher start pid $$" >> "$R/queue.log"
"$PY" -I -B "$D/h512/train/train_h512_gpu.py" train --plan "$D/h512/train/plans/$arm.json" --run-dir "$R" --resume --log-every 5000 "$@" >> "$R/trainer.out" 2>&1
rc=$?; echo "$(date '+%F %T') trainer exit $rc" >> "$R/queue.log"
if [ $rc -eq 0 ] && grep -q "EXIT plan complete" "$R/log.txt"; then touch "$R/DONE"; fi
exit $rc
