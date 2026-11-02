#!/usr/bin/env bash
# R14 A1: P5 fix proof - guard check, 1,000-row relabel with the original FEN sidecar, label compare vs job1, full audit.
set -u
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
P5=D:/grok-pc-data/dwqww/.claude/worktrees/o13-p5/opus_r13/p5
POS='D:\grok-pc-data\r11_nnue\astra\forge_filtered.pos'
FEN='D:\o14a\p5\forge_filtered.fen'
PROBE='C:\o13\p5\forge_data_probe.exe'
for d in /d/o14a/p5/job_guardcheck /d/o14a/p5/job_fix1k /d/o14a/p5/compare_fix1k.json /d/o14a/p5/audit_full.json; do
  if [ -e "$d" ]; then echo "exists: $d - refusing"; exit 2; fi
done
date '+start %F %T'
"$PY" -I -B $P5/relabel_job.py run --pos "$POS" --probe "$PROBE" --job 'D:\o14a\p5\job_guardcheck' --run-id r14p5-guard \
  --allow-reconstructed --rows 10 --shard-size 10 --workers 1 --mask 0xC
echo "guard exit $? (must be non-zero); job dir created: $([ -e /d/o14a/p5/job_guardcheck ] && echo yes || echo no)"
"$PY" -I -B $P5/relabel_job.py run --pos "$POS" --probe "$PROBE" --job 'D:\o14a\p5\job_fix1k' --run-id r14p5-20261102-fix1k \
  --sidecar "$FEN" --sidecar-origin original_full_fen --rows 1000 --shard-size 1000 --nodes 20000 --workers 1 --hash-mb 1 --mask 0xC
echo "relabel exit $?"
date '+relabel done %F %T'
"$PY" -I -B $P5/prove_sidecar.py compare --old 'C:\o13\p5\job1\shards\shard_00000' --new 'D:\o14a\p5\job_fix1k\shards\shard_00000' \
  --fen "$FEN" --count 1000 --out 'D:\o14a\p5\compare_fix1k.json'
echo "compare exit $?"
"$PY" -I -B $P5/prove_sidecar.py audit --pos "$POS" --fen "$FEN" --out 'D:\o14a\p5\audit_full.json' --job1-rows 440000
echo "audit exit $?"
date '+end %F %T'
