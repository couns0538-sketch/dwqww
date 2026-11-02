#!/usr/bin/env bash
# R14 A4: H256 parity after CR patch d884c23b, fresh work dirs (never reused), legal-only FENs, fresh cargo build.
set -uo pipefail
export PATH=/c/msys64/ucrt64/bin:$PATH OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
P4=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p4/opus_r13/p4
B=/d/o14a/p4/target_mock/release/forge-v2-bullet.exe
F=/d/o14a/p4/fens10k_legal.txt
for d in /d/o14a/p4/parity_h256 /d/o14a/p4/parity_h256_mutate; do
  if [ -e "$d" ]; then echo "work dir $d exists: refusing (fresh dirs only)"; exit 2; fi
done
date '+start %F %T'
bash $P4/parity_v2.sh /d/o14a/p4/parity_h256 $F $B /c/o13/p4/v2_eval_avx2.exe /c/o13/p4/v2_eval_sse.exe; echo "parity exit $?"
PARITY_MUTATE=1 bash $P4/parity_v2.sh /d/o14a/p4/parity_h256_mutate $F $B /c/o13/p4/v2_eval_avx2.exe /c/o13/p4/v2_eval_sse.exe; echo "mutated parity exit $? (must be 1)"
date '+end %F %T'
