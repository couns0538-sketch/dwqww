#!/usr/bin/env bash
# gpu_queue.sh - JOB E phase 2: run GPU jobs one after another so the GPU is never idle and never shared.
# Jobs are the lines of _work/runs/gpu_queue.txt (one bash command per line); lines may be appended while the queue
# runs. Log: _work/runs/gpu_queue.log, output of job N: _work/runs/gpu_queue_jobN.out.
# Stop after the current job with: touch _work/runs/STOP_GPU_QUEUE
set -u
D=/d/forge_jobs_20261111/h512E
Q="$D/_work/runs/gpu_queue.txt"; L="$D/_work/runs/gpu_queue.log"; n=0
echo "$(date '+%F %T') gpu queue start pid $$" >> "$L"
while [ ! -f "$D/_work/runs/STOP_GPU_QUEUE" ]; do
  total=$(grep -c . "$Q" 2>/dev/null); total=${total:-0}
  if [ "$n" -lt "$total" ]; then
    n=$((n + 1)); line=$(sed -n "${n}p" "$Q")
    echo "$(date '+%F %T') job $n start: $line" >> "$L"
    bash -c "$line" >> "$D/_work/runs/gpu_queue_job$n.out" 2>&1
    echo "$(date '+%F %T') job $n exit $?" >> "$L"
  else
    sleep 10
  fi
done
echo "$(date '+%F %T') gpu queue stopped by flag" >> "$L"
