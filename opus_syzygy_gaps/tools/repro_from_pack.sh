#!/usr/bin/env bash
# repro_from_pack.sh <tag> <Build B sha256> - reproduction from the pack alone: a fresh tree from the lock source, the P6 patch and this pack's patch, both with -F0, then the kit recipe.
#   macros off must give the parent exe 150374FF byte for byte, macros on must give the Build B of final_freeze.sh byte for byte. Also: the fresh tree equals the HEAD of out/src/cand.
# Output out/builds/repro_<tag>.txt. Exits by itself.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
tag=$1; want=$2
O=$J/out/builds/repro_$tag.txt
SRC=$J/out/src/repro_$tag
PARENT_SHA=150374FF4B9132B99B48E9BA6A51B36B89E22014C61CEC3053D1F4F17B87D99F
DEFS='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
say() { echo "$*" | tee -a "$O" | cut -c1-220; }
mkdir -p "$SRC"
tar -x -C "$SRC" -f "$J/out/src/lock_d4f4312.tar"
say "lock source: $(find "$SRC/src" "$SRC/include" -type f | wc -l) files"
( cd "$SRC" && patch -p1 -F0 --no-backup-if-mismatch < "$J/repo/opus_r13/p6/syzygy_port.patch" > "$O.p6.log" ) || { say "FAIL P6 patch rejected"; exit 1; }
say "P6 patch md5 $(md5sum "$J/repo/opus_r13/p6/syzygy_port.patch" | cut -c1-32), applied with -F0"
( cd "$SRC" && patch -p1 -F0 --no-backup-if-mismatch < "$J/repo/opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch" > "$O.gaps.log" ) || { say "FAIL pack patch rejected"; exit 1; }
say "pack patch md5 $(md5sum "$J/repo/opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch" | cut -c1-32), applied with -F0"
find "$SRC" -name '*.rej' | head -3 >> "$O"
say "fresh tree against out/src/cand HEAD: $(diff -r "$SRC/src" "$J/out/src/cand/src" > /dev/null && diff -r "$SRC/include" "$J/out/src/cand/include" > /dev/null && echo SAME || echo DIFFERENT)"
say "macros off: $(ps "$T/kit_build.ps1" -SrcDir "$W\\out\\src\\repro_$tag" -Tag "repro_A_$tag" -WantSha "$PARENT_SHA" | tail -1)"
say "macros on: $(ps "$T/kit_build.ps1" -SrcDir "$W\\out\\src\\repro_$tag" -Tag "repro_B_$tag" -Defines "$DEFS" -WantSha "$want" | tail -1)"
say "end $(date)"
