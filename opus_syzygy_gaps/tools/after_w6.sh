#!/usr/bin/env bash
# after_w6.sh <tag> - the after_w6 line: trial_w6 source + P6 port = its parent; + this job's patch = candidate. Builds with the kit recipe and the six trial_w6 defines:
#   parent (port on w6), Build A' (macros off, must equal that parent byte for byte), Build B' (macros on, options 0), pins of B' without and with tables, 12k identity of B' against the parent.
# Writes patches/syzygy_port_and_gaps_after_w6.patch and out/builds/after_w6_<tag>.txt, and checks that this one patch on a fresh trial_w6 tree gives the same tree.
# The w6 exe itself is compared by pins (the port adds options, so no byte identity with it).
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
tag=$1
SP='FORGE_SPD_TT_NOTLS=1,FORGE_SPD_NO_ZERO_MOVELISTS=2,FORGE_SEARCH_SPEED2=1,FORGE_SPD_PREFETCH_EARLY=1,FORGE_SPD_SLIDER_PEXT=1,FORGE_SPD_NNUE_ZMM=1'
ALL='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
O=$J/out/builds/after_w6_$tag.txt
SRC=$J/out/src
P=$J/repo/opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch
PW6=$J/repo/opus_syzygy_gaps/patches/syzygy_port_and_gaps_after_w6.patch
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
say() { echo "$*" | tee -a "$O" | cut -c1-200; }
TREE=w6p6g_$tag
mkdir -p "$SRC/$TREE"
tar -x -C "$SRC/$TREE" -f "$SRC/lock_d4f4312.tar"
( cd "$SRC/$TREE" && patch -p1 -F0 --no-backup-if-mismatch < ../trial_w6.patch > /dev/null && patch -p1 -F0 --no-backup-if-mismatch < "$J/repo/opus_r13/p6/syzygy_port.patch" > /dev/null \
  && git init -q . && git config core.autocrlf false && git config user.name couns0538-sketch && git config user.email couns0538@gmail.com && git add -A && git commit -q -m "w6 + port" )
PARENT="$W\\out\\src\\$TREE"
say "parent tree $TREE w6 + port, head $(git -C "$SRC/$TREE" log -1 --format=%h)"
ps "$T/kit_build.ps1" -SrcDir "$PARENT" -Tag "w6p6_parent_$tag" -Defines "$SP" | tail -1 | cut -c1-160
PSHA=$(sha256sum "$J/out/builds/w6p6_parent_$tag/forge_w6p6_parent_$tag.exe" | cut -c1-64 | tr a-z A-Z)
say "parent sha256 $PSHA"
# no pipe on patch: a rejected hunk must stop the line (R3 finding 8)
( cd "$SRC/$TREE" && patch -p1 -F0 --no-backup-if-mismatch < "$P" > "$O.patch.log" ) || { say "FAIL gaps patch rejected, see $O.patch.log"; exit 1; }
if find "$SRC/$TREE" -name '*.rej' | grep -q .; then say "FAIL rejected hunks"; exit 1; fi
( cd "$SRC/$TREE" && git add -A && git commit -q -m "gaps" ) || { say "FAIL commit"; exit 1; }
say "gaps applied with -F0, head $(git -C "$SRC/$TREE" log -1 --format=%h)"
say "A' $(ps "$T/kit_build.ps1" -SrcDir "$PARENT" -Tag "w6p6_A_$tag" -Defines "$SP" -WantSha "$PSHA" | tail -1)"
ps "$T/kit_build.ps1" -SrcDir "$PARENT" -Tag "w6p6_B_$tag" -Defines "$SP,$ALL" | tail -1 | cut -c1-160
BX="$J/out/builds/w6p6_B_$tag/forge_w6p6_B_$tag.exe"
say "B' sha256 $(sha256sum "$BX" | cut -c1-64)"
BW="$W\\out\\builds\\w6p6_B_$tag\\forge_w6p6_B_$tag.exe"
PW="$W\\out\\builds\\w6p6_parent_$tag\\forge_w6p6_parent_$tag.exe"
WT="$W\\repo\\opus_syzygy_gaps\\tools"
ps "$T/pinned.ps1" -Exe 'C:\Python315\python.exe' -ArgLine "-I -B $WT\\pins.py $BW $W\\out\\builds\\w6p6_B_$tag\\pins_off.json --expect lock" -Log "$W\\out\\builds\\w6p6_B_$tag\\pins_off.out"
say "B' pins off: $(tail -1 "$J/out/builds/w6p6_B_$tag/pins_off.out")"
ps "$T/pinned.ps1" -Exe 'C:\Python315\python.exe' -ArgLine "-I -B $WT\\pins.py $BW $W\\out\\builds\\w6p6_B_$tag\\pins_tb.json --expect p6path --tables D:\\syzygy345 --no-net-off" -Log "$W\\out\\builds\\w6p6_B_$tag\\pins_tb.out"
say "B' pins tables: $(tail -1 "$J/out/builds/w6p6_B_$tag/pins_tb.out")"
ps "$T/identity_runs.ps1" -Exe "$PW" -Tag "w6p6_parent_$tag" -Sets 'net_on,tb_roots,tb_clock' -Jobs 3 > /dev/null
ps "$T/identity_runs.ps1" -Exe "$BW" -Tag "w6p6_B_$tag" -Sets 'net_on,tb_roots,tb_clock' -Jobs 3 > /dev/null
for s in net_on tb_roots tb_clock; do say "$s: $(python -I -B "$T/compare_runs.py" "$J/out/ident/w6p6_parent_$tag/$s.jsonl" "$J/out/ident/w6p6_B_$tag/$s.jsonl" | cut -c1-200)"; done
# P6-parent identity of the same sets: the speed switches must not change a node
for s in net_on tb_roots tb_clock; do say "$s against the P6 parent 150374ff: $(python -I -B "$T/compare_runs.py" "$J/out/ident/parent_150374ff/$s.jsonl" "$J/out/ident/w6p6_B_$tag/$s.jsonl" | cut -c1-200)"; done
mkdir -p "$SRC/w6_only_$tag"; tar -x -C "$SRC/w6_only_$tag" -f "$SRC/lock_d4f4312.tar"; ( cd "$SRC/w6_only_$tag" && patch -p1 -F0 --no-backup-if-mismatch < ../trial_w6.patch > /dev/null )
( cd "$SRC" && diff -ruN --strip-trailing-cr "w6_only_$tag/include" "$TREE/include"; diff -ruN --strip-trailing-cr "w6_only_$tag/src" "$TREE/src" ) > "$PW6"
say "after_w6 patch lines $(wc -l < "$PW6") md5 $(md5sum "$PW6" | cut -c1-32)"
mkdir -p "$SRC/w6_check_$tag"; tar -x -C "$SRC/w6_check_$tag" -f "$SRC/lock_d4f4312.tar"
( cd "$SRC/w6_check_$tag" && patch -p1 -F0 --no-backup-if-mismatch < ../trial_w6.patch > /dev/null && patch -p1 -F0 --no-backup-if-mismatch < "$PW6" > /dev/null )
say "after_w6 patch on a fresh trial_w6 tree: $(diff -r --strip-trailing-cr "$SRC/w6_check_$tag/src" "$SRC/$TREE/src" > /dev/null && diff -r --strip-trailing-cr "$SRC/w6_check_$tag/include" "$SRC/$TREE/include" > /dev/null && echo SAME TREE || echo DIFFERENT)"
say "end $(date)"
echo done
