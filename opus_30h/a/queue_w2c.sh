#!/usr/bin/env bash
# queue_w2c.sh - Opus 30-h job, second GPU window (2026-11-04). Never edited while it runs (bash reads it lazily).
# After run 8 ends: run 9 = run 7's recipe (KB16 rank4x4, 200 superbatches, lr 2e-5, wdl 0.4) with another seed
# (30109): one sample of run-to-run noise, the yardstick for the KB8 / KB16 / KB32 differences. Warm start from the
# lock (init_lockkb16, proven byte-identical in warmproof04). Outputs on C:\o30g\gpu. Idle, CPUs 3-5 (0x38).
set -u
. /d/o30/wt/opus_30h/tools/idle.sh
o30_pin_self 0x38 || { echo "queue_w2c: cannot pin to Idle / CPUs 3-5 (fail closed)"; exit 78; }
until grep -q ' end: ' /c/o30g/gpu/r8_kb32short.guard.log 2>/dev/null; do sleep 15; done
sleep 20
echo "$(date '+%F %T') run 8 ended (guard log end line seen); starting run 9 (KB16, seed 30109)"
GUARD_MASK=0x38 BULLET_EXE='D:\o30\target_rocm4\release\forge-v2-bullet.exe' O30_INIT_DIR='D:\o30\gpu\init_lockkb16' \
    O30_CLIP=7.99 O30_DECAY=0 cmd //d //c 'D:\o30\wt\opus_30h\a\gpu_run_o30c.bat' r9_kb16seed rank4x4 0 256 200 1024 2 30109 0.00002 0.4 8
echo "run 9 exit $? $(date '+%F %T')"
