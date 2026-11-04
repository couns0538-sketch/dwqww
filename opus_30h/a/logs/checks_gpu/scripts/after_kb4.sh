#!/usr/bin/env bash
# after_kb4.sh - checks of the GPU-trained v2 nets (2026-11-04): waits for the KB4 chain's end marker (CPU 0 is used by
# one check at a time), then runs the KB8 chain, then probe repeats (rep1, rep2) of both nets for run-to-run noise.
# Every step goes through step.sh (Idle, CPU 0, trainer check, deadline 14:03). Gives up waiting at GIVE_UP (13:40).
set -u
S=D:/o30/checks_gpu/scripts
KB4=D:/o30/checks_gpu/o30_gpu_kb4warm_r2/chain.txt
GIVE_UP="${GIVE_UP:-13:40}"
give_s=$(date -d "today $GIVE_UP" +%s)
while ! grep -q "chain o30_gpu_kb4warm_r2 end" "$KB4" 2>/dev/null; do
  if [ "$(date +%s)" -ge "$give_s" ]; then echo "after_kb4: KB4 chain not ended by $GIVE_UP ($(date '+%H:%M:%S')) - nothing started"; exit 1; fi
  sleep 15
done
echo "after_kb4: KB4 chain ended, starting KB8 at $(date '+%H:%M:%S')"
bash "$S/chain.sh" o30_gpu_kb8warm_r3 D:/o30/nets/o30_gpu_kb8warm_r3/o30_gpu_kb8warm_r3.nnue2 D:/o30/nets/lockv2/lock_kbrank4x2_ob8.nnue2 \
  > D:/o30/checks_gpu/o30_gpu_kb8warm_r3/chain.txt 2>&1
echo "after_kb4: KB8 chain rc=$? at $(date '+%H:%M:%S')"
for rep in rep1 rep2; do
  bash "$S/chain.sh" o30_gpu_kb4warm_r2 D:/o30/nets/o30_gpu_kb4warm_r2/o30_gpu_kb4warm_r2.nnue2 D:/o30/nets/lockv2/lock_kbrank4_ob8.nnue2 "$rep" \
    >> D:/o30/checks_gpu/o30_gpu_kb4warm_r2/chain_$rep.txt 2>&1
  echo "after_kb4: KB4 $rep rc=$? at $(date '+%H:%M:%S')"
  bash "$S/chain.sh" o30_gpu_kb8warm_r3 D:/o30/nets/o30_gpu_kb8warm_r3/o30_gpu_kb8warm_r3.nnue2 D:/o30/nets/lockv2/lock_kbrank4x2_ob8.nnue2 "$rep" \
    >> D:/o30/checks_gpu/o30_gpu_kb8warm_r3/chain_$rep.txt 2>&1
  echo "after_kb4: KB8 $rep rc=$? at $(date '+%H:%M:%S')"
done
echo "after_kb4: all done at $(date '+%H:%M:%S')"
