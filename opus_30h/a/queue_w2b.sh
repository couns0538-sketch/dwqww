#!/usr/bin/env bash
# queue_w2b.sh - Opus 30-h job, second GPU window (2026-11-04). Never edited while it runs (bash reads it lazily).
# After run 7 ends: lr-0 warm proof of the 32-bucket init (rank4x8) on the 16/32-bucket build, then run 8 (32 king
# buckets, run 5's recipe: 200 superbatches, lr 2e-5, wdl 0.4) under the guard, only if the proof compared
# byte-identical. Outputs on C:\o30g\gpu (D: near its 50 GB floor); proof log in the branch. Idle, CPUs 3-5 (0x38).
set -u
G=/c/o30g/gpu
A=/d/o30/wt/opus_30h/a
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SPU=/f/nnue_pytorch/venv/Lib/site-packages
export HIP_PATH='F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel'
export PATH="$SPU/_rocm_sdk_libraries_gfx110X_all/bin:$SPU/_rocm_sdk_devel/bin:$PATH"
. /d/o30/wt/opus_30h/tools/idle.sh
o30_pin_self 0x38 || { echo "queue_w2b: cannot pin to Idle / CPUs 3-5 (fail closed)"; exit 78; }

until grep -q ' end: ' /d/o30/gpu/r7_kb16short.guard.log 2>/dev/null; do sleep 15; done
sleep 20
echo "$(date '+%F %T') run 7 ended (guard log end line seen)"

tag=warmproof05_kb32; tdir=target_rocm4; kmap=rank4x8; init='D:\o30\gpu\init_lockkb32'
ref=/d/o30/nets/lockv2/lock_kbrank4x8_ob8.nnue2
exe=/d/o30/$tdir/release/forge-v2-bullet.exe; out=$G/$tag; L=$A/logs/gpu/$tag.out
[ -e "$out" ] && { echo "refusing: $out exists"; exit 1; }
[ -e "$L" ] && { echo "refusing: $L exists"; exit 1; }
busy=$($PY -I -B D:/o30/gpu/npt_busy.py)
[ "$busy" = "0" ] || { echo "$(date '+%T') npt-like process present ($busy): nothing started"; exit 2; }
{
    echo "date $(date '+%F %T') host $(hostname) tag $tag"
    echo "exe D:\\o30\\$tdir\\release\\forge-v2-bullet.exe md5 $(md5sum $exe | cut -c1-32) sha256 $(sha256sum $exe | cut -c1-64)"
    echo "branch head at start $(git -C /d/o30/wt rev-parse HEAD); main.rs md5 in the worktree $(md5sum $A/forge_v2_bullet_o30/src/main.rs | cut -c1-32)"
    echo "env O30_INIT_DIR=$init O30_CLIP=7.99 O30_DECAY=0 HIP_PATH=$HIP_PATH; Idle, affinity 0x38"
    echo "cmd forge-v2-bullet.exe r D:/o30/data C:/o30g/gpu/$tag $kmap 0 256 1 8 2 30201 0 0.4 8"
    O30_INIT_DIR="$init" O30_CLIP=7.99 O30_DECAY=0 $exe r D:/o30/data "C:/o30g/gpu/$tag" $kmap 0 256 1 8 2 30201 0 0.4 8 2>&1 \
        | sed 's/\x1b\[[0-9;]*m//g' | grep -a -v 'Estimated time'
    echo "trainer exit ${PIPESTATUS[0]}"
    ck=$(ls -d "$out"/*-1 2>/dev/null | head -1)
    $PY -I -B "$A/export_v2r.py" "$ck/quantised.bin" "$out/warm.nnue2" --kb-map $kmap
    echo "export exit $?"
    echo "md5 exported  $(md5sum "$out/warm.nnue2" | cut -c1-32) $out/warm.nnue2"
    echo "md5 reference $(md5sum "$ref" | cut -c1-32) $ref"
    if cmp "$out/warm.nnue2" "$ref"; then echo "COMPARE: byte-identical -> PASS"; else echo "COMPARE: differ -> FAIL"; fi
    echo "end $(date '+%F %T')"
} > "$L" 2>&1
echo "== $tag"; grep -a -E 'AdamW|warm start|trainer exit|export exit|md5 |COMPARE' "$L"
if ! grep -q 'COMPARE: byte-identical -> PASS' "$L"; then
    echo "$(date '+%F %T') KB32 warm proof not PASS: run 8 NOT started"
    exit 3
fi
echo "$(date '+%F %T') starting run 8 (KB32 rank4x8, 200 superbatches, lr 2e-5) on C:\\o30g\\gpu"
GUARD_MASK=0x38 BULLET_EXE='D:\o30\target_rocm4\release\forge-v2-bullet.exe' O30_INIT_DIR='D:\o30\gpu\init_lockkb32' \
    O30_CLIP=7.99 O30_DECAY=0 cmd //d //c 'D:\o30\wt\opus_30h\a\gpu_run_o30c.bat' r8_kb32short rank4x8 0 256 200 1024 2 30108 0.00002 0.4 8
echo "run 8 exit $? $(date '+%F %T')"
