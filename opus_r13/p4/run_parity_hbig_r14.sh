#!/usr/bin/env bash
# R14 A4: parity above H256. Per H: fresh work dir, random nets of width H pre-generated with the R13 seeds
# (13451 / 13452 / 13453 for stages a / b / c), then CR's parity_v2.sh (md5 9c124cc3, unchanged; it keeps an existing net
# and always rebuilds ref_<s>.txt) with the H harness builds; planted bug once at H1536 in its own fresh dir.
set -u
export PATH=/c/msys64/ucrt64/bin:$PATH OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
P4=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p4/opus_r13/p4
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
B=/d/o14a/p4/target_mock/release/forge-v2-bullet.exe
F=/d/o14a/p4/fens10k_legal.txt
echo "parity_v2.sh md5 $(md5sum $P4/parity_v2.sh | cut -c1-8) (CR: 9c124cc3)"
date '+start %F %T'
run() {  # $1 = H, $2 = work dir, $3 = PARITY_MUTATE
  local H=$1 W=$2
  if [ -e "$W" ]; then echo "work dir $W exists: refusing (fresh dirs only)"; return 2; fi
  mkdir -p "$W"
  for s in a b c; do
    seed=$((13450 + $(printf '%d' "'$s") - 96))
    "$PY" -I -B $P4/make_random_net.py $s "$(cygpath -w "$W/rand_$s.nnue2")" --hidden $H --seed $seed || return 1
  done
  PARITY_MUTATE=$3 bash $P4/parity_v2.sh "$W" $F $B /d/o14a/p4/v2_eval_avx2_h$H.exe /d/o14a/p4/v2_eval_sse_h$H.exe
}
for H in 768 1024 1536; do
  run $H /d/o14a/p4/parity_h$H 0; echo "H$H parity exit $?"
done
run 1536 /d/o14a/p4/parity_h1536_mutate 1; echo "H1536 mutated parity exit $? (must be 1)"
date '+end %F %T'
