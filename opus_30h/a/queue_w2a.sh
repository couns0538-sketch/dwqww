#!/usr/bin/env bash
# queue_w2a.sh - Opus 30-h job, second GPU window (2026-11-04). Never edited while it runs (bash reads it lazily).
# After run 6 ends: three lr-0 warm-start proofs (1 superbatch x 8 batches, lr 0, then export and byte compare with
# the lock net written in the same king layout):
#   warmproof02_rocm2  - CR item 11: the exe that trained runs 2-6 (D:\o30\target_rocm2), KB4
#   warmproof03_rocm3  - CR items 10/11: the item-10 build (D:\o30\target_rocm3), KB4 ("with both set it behaves as before")
#   warmproof04_kb16   - the 16-bucket build (D:\o30\target_rocm4), KB16 init from the lock
# then run 7 (16 king buckets rank4x4, run 5's recipe: 200 superbatches, lr 2e-5, wdl 0.4) under the GPU guard,
# only if warmproof04 compared byte-identical. Idle, CPUs 3-5 (0x38) for everything; skips while an npt-like process runs.
set -u
G=/d/o30/gpu
A=/d/o30/wt/opus_30h/a
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
SPU=/f/nnue_pytorch/venv/Lib/site-packages
export HIP_PATH='F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel'
export PATH="$SPU/_rocm_sdk_libraries_gfx110X_all/bin:$SPU/_rocm_sdk_devel/bin:$PATH"
. /d/o30/wt/opus_30h/tools/idle.sh
o30_pin_self 0x38 || { echo "queue_w2a: cannot pin to Idle / CPUs 3-5 (fail closed)"; exit 78; }

until grep -q ' end: ' $G/r6_kb8lr3.guard.log 2>/dev/null; do sleep 15; done
sleep 20
echo "$(date '+%F %T') run 6 ended (guard log end line seen)"

wp() {  # wp <tag> <target folder name> <king map> <init dir (Windows)> <reference .nnue2 (MSYS path)>
    local tag=$1 tdir=$2 kmap=$3 init=$4 ref=$5
    local exe=/d/o30/$tdir/release/forge-v2-bullet.exe out=$G/$tag L=$A/logs/gpu/$tag.out
    [ -e "$out" ] && { echo "refusing: $out exists"; return 1; }
    [ -e "$L" ] && { echo "refusing: $L exists"; return 1; }
    local busy
    busy=$($PY -I -B D:/o30/gpu/npt_busy.py)
    [ "$busy" = "0" ] || { echo "$(date '+%T') npt-like process present ($busy): skip $tag"; return 1; }
    {
        echo "date $(date '+%F %T') host $(hostname) tag $tag"
        echo "exe D:\\o30\\$tdir\\release\\forge-v2-bullet.exe md5 $(md5sum $exe | cut -c1-32) sha256 $(sha256sum $exe | cut -c1-64)"
        echo "branch head at start $(git -C /d/o30/wt rev-parse HEAD); main.rs md5 in the worktree $(md5sum $A/forge_v2_bullet_o30/src/main.rs | cut -c1-32)"
        echo "env O30_INIT_DIR=$init O30_CLIP=7.99 O30_DECAY=0 HIP_PATH=$HIP_PATH; Idle, affinity 0x38"
        echo "cmd forge-v2-bullet.exe r D:/o30/data D:/o30/gpu/$tag $kmap 0 256 1 8 2 30201 0 0.4 8"
        O30_INIT_DIR="$init" O30_CLIP=7.99 O30_DECAY=0 $exe r D:/o30/data "D:/o30/gpu/$tag" $kmap 0 256 1 8 2 30201 0 0.4 8 2>&1 \
            | sed 's/\x1b\[[0-9;]*m//g' | grep -a -v 'Estimated time'
        echo "trainer exit ${PIPESTATUS[0]}"
        local ck
        ck=$(ls -d "$out"/*-1 2>/dev/null | head -1)
        $PY -I -B "$A/export_v2r.py" "$ck/quantised.bin" "$out/warm.nnue2" --kb-map $kmap
        echo "export exit $?"
        echo "md5 exported  $(md5sum "$out/warm.nnue2" | cut -c1-32) $out/warm.nnue2"
        echo "md5 reference $(md5sum "$ref" | cut -c1-32) $ref"
        if cmp "$out/warm.nnue2" "$ref"; then echo "COMPARE: byte-identical -> PASS"; else echo "COMPARE: differ -> FAIL"; fi
        echo "end $(date '+%F %T')"
    } > "$L" 2>&1
    echo "== $tag"; grep -a -E 'AdamW|warm start|trainer exit|export exit|md5 |COMPARE' "$L"
    grep -q 'COMPARE: byte-identical -> PASS' "$L"
}

wp warmproof02_rocm2 target_rocm2 rank4 'D:\o30\gpu\init_lockkb4' /d/o30/nets/lockv2/lock_kbrank4_ob8.nnue2
wp warmproof03_rocm3 target_rocm3 rank4 'D:\o30\gpu\init_lockkb4' /d/o30/nets/lockv2/lock_kbrank4_ob8.nnue2
if ! wp warmproof04_kb16 target_rocm4 rank4x4 'D:\o30\gpu\init_lockkb16' /d/o30/nets/lockv2/lock_kbrank4x4_ob8.nnue2; then
    echo "$(date '+%F %T') KB16 warm proof not PASS: run 7 NOT started"
    exit 3
fi
echo "$(date '+%F %T') starting run 7 (KB16 rank4x4, 200 superbatches, lr 2e-5)"
GUARD_MASK=0x38 BULLET_EXE='D:\o30\target_rocm4\release\forge-v2-bullet.exe' O30_INIT_DIR='D:\o30\gpu\init_lockkb16' \
    O30_CLIP=7.99 O30_DECAY=0 cmd //d //c 'D:\o30\wt\opus_30h\a\gpu_run_o30.bat' r7_kb16short rank4x4 0 256 200 1024 2 30107 0.00002 0.4 8
echo "run 7 exit $? $(date '+%F %T')"
