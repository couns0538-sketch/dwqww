#!/usr/bin/env bash
# after_reps.sh - checks of the GPU-trained v2 nets (2026-11-04): waits for after_kb4.sh's "all done" marker (one check at
# a time on CPU 0), then one probe per net at movetime 500 ms on 100 positions (tag mt500), deadline-guarded by step.sh.
set -u
S=D:/o30/checks_gpu/scripts
M=D:/o30/checks_gpu/after_kb4.txt
GIVE_UP="${GIVE_UP:-13:52}"
give_s=$(date -d "today $GIVE_UP" +%s)
while ! grep -q "after_kb4: all done" "$M" 2>/dev/null; do
  if grep -q "nothing started" "$M" 2>/dev/null; then echo "after_reps: after_kb4 gave up - nothing started"; exit 1; fi
  if [ "$(date +%s)" -ge "$give_s" ]; then echo "after_reps: repeats not done by $GIVE_UP ($(date '+%H:%M:%S')) - nothing started"; exit 1; fi
  sleep 15
done
echo "after_reps: repeats done, starting mt500 probes at $(date '+%H:%M:%S')"
bash "$S/probe_extra.sh" o30_gpu_kb4warm_r2 D:/o30/nets/o30_gpu_kb4warm_r2/o30_gpu_kb4warm_r2.nnue2 D:/o30/nets/lockv2/lock_kbrank4_ob8.nnue2 mt500 100 500
bash "$S/probe_extra.sh" o30_gpu_kb8warm_r3 D:/o30/nets/o30_gpu_kb8warm_r3/o30_gpu_kb8warm_r3.nnue2 D:/o30/nets/lockv2/lock_kbrank4x2_ob8.nnue2 mt500 100 500
echo "after_reps: all done at $(date '+%H:%M:%S')"
