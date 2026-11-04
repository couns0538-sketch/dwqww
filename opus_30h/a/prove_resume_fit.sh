#!/usr/bin/env bash
# prove_resume_fit.sh <tag> [mask] - Opus 30-h job: o30_fit.py resume proof. Run U trains 6.5M positions uninterrupted;
# run I trains the same configuration but stops at a deadline ~60 s after its start (a real interruption: the trainer
# saves last.pt and exits), then is resumed to the end. PASS = U and I end with bit-identical weights (w1, b1, w2, b2)
# and the same step / positions / chunk state (1 torch thread on the CPU is deterministic and the data stream depends
# only on (seed, chunk)). Runs D:/o30/runs/rz_<tag>_u and _i (refused when they exist); Idle on <mask> (default 0x2).
set -uo pipefail
. "$(cd "$(dirname "$0")" && pwd)/../tools/idle.sh"; o30_pin_self 0x3 || { echo "cannot pin to Idle / CPUs 0-1 (fail closed)" >&2; exit 78; }
tag="$1"; mask="${2:-0x2}"
A=$(cd "$(dirname "$0")" && pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
common="--init lock --kb-map rank4 --ob 8 --lr 2e-5 --lr-out-mult 2 --lr-end 1e-7 --positions 6.5e6 --mix 8 --save-minutes 1000 --seed 77"
for r in u i; do [ -e "D:/o30/runs/rz_${tag}_$r" ] && { echo "refusing: rz_${tag}_$r exists"; exit 2; }; done
bash "$A/fit_bg.sh" "rz_${tag}_u" "$mask" $common
until_t=$(date -d '+75 seconds' '+%Y-%m-%dT%H:%M')
bash "$A/fit_bg.sh" "rz_${tag}_i" "$mask" $common --until "$until_t"
grep -h "final-" "D:/o30/logs/rz_${tag}_i.out" | tail -1
bash "$A/fit_resume.sh" "rz_${tag}_i" "$mask"
"$PY" -I -B - "D:/o30/runs/rz_${tag}_u/last.pt" "D:/o30/runs/rz_${tag}_i/last.pt" <<'EOF'
import sys
import torch
u, i = (torch.load(p, weights_only=False) for p in sys.argv[1:3])
same = all(torch.equal(u['params'][k], i['params'][k]) for k in u['params'])
su = {k: u['state'][k] for k in ('step', 'positions', 'chunk', 'in_chunk')}
si = {k: i['state'][k] for k in ('step', 'positions', 'chunk', 'in_chunk')}
print('U state', su)
print('I state', si)
ok = same and su == si
print('RESUME PROOF ' + ('PASS: bit-identical weights and state' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
EOF
