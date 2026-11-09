#!/usr/bin/env bash
# final_freeze.sh <tag> - the freeze proof of the HEAD of out/src/cand. Everything pinned, nothing queued, exits by itself. Result lines in out/builds/final_<tag>.txt.
#   patch = git diff against the P6 parent; preprocess compare with the macros off; Build A (kit recipe, macros off) must be the parent exe byte for byte;
#   Build B (kit recipe, macros on, options 0) pc1 = pc2; pins of B without and with tables; identity sets of B against the parent; warm identity of B against the parent,
#   without tables (12k FENs) and with tables (12k FENs, clock fixture); bench signature of B per option value, without and with tables.
# The after_w6 line is a separate tool (after_w6.sh).
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
tag=$1
O=$J/out/builds/final_$tag.txt
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
say() { echo "$*" | tee -a "$O" | cut -c1-220; }
PARENT_SHA=150374FF4B9132B99B48E9BA6A51B36B89E22014C61CEC3053D1F4F17B87D99F
PARENT_EXE="$W\\out\\builds\\p6_parent_pc1\\forge_p6_parent_pc1.exe"
DEFS='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
CAND="$W\\out\\src\\cand"
C=$J/out/src/cand
say "head $(git -C "$C" log -1 --format=%H) changed files in tree $(git -C "$C" status --short | wc -l)"
say "patch from parent md5 $(git -C "$C" diff ded9684 HEAD | md5sum | cut -c1-32) pack patch md5 $(md5sum "$J/repo/opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch" | cut -c1-32)"
say "parent exe sha256 $(sha256sum "$J/out/builds/p6_parent_pc1/forge_p6_parent_pc1.exe" | cut -c1-64)"
say "preprocess, macros off: $(ps "$T/preprocess_diff.ps1" -Parent "$W\\out\\src\\p6_port" -Cand "$CAND" | tail -1)"
say "preprocess, macros on, code differs as expected: $(ps "$T/preprocess_diff.ps1" -Parent "$W\\out\\src\\p6_port" -Cand "$CAND" -Defines "$DEFS" | tail -1)"
say "Build A: $(ps "$T/kit_build.ps1" -SrcDir "$CAND" -Tag "buildA_c$tag" -WantSha "$PARENT_SHA" | tail -1)"
say "Build A sha256 $(sha256sum "$J/out/builds/buildA_c$tag/forge_buildA_c$tag.exe" | cut -c1-64)"
ps "$T/kit_build.ps1" -SrcDir "$CAND" -Tag "buildB_c${tag}_pc1" -Defines "$DEFS" | tail -1 | cut -c1-200
BX=$J/out/builds/buildB_c${tag}_pc1/forge_buildB_c${tag}_pc1.exe
B1=$(sha256sum "$BX" | cut -c1-64 | tr a-z A-Z)
say "Build B pc1 sha256 $B1 md5 $(md5sum "$BX" | cut -c1-32)"
say "Build B pc2: $(ps "$T/kit_build.ps1" -SrcDir "$CAND" -Tag "buildB_c${tag}_pc2" -Defines "$DEFS" -WantSha "$B1" | tail -1)"
say "Build B pc2 sha256 $(sha256sum "$J/out/builds/buildB_c${tag}_pc2/forge_buildB_c${tag}_pc2.exe" | cut -c1-64)"
BW="$W\\out\\builds\\buildB_c${tag}_pc1\\forge_buildB_c${tag}_pc1.exe"
BD="$W\\out\\builds\\buildB_c${tag}_pc1"
BU=$J/out/builds/buildB_c${tag}_pc1
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\pins_off.json --expect lock" -Log "$BD\\pins_off.out"
say "B pins, no tables: $(tail -1 "$BU/pins_off.out")"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\pins_tb.json --expect p6path --tables D:\\syzygy345 --no-net-off" -Log "$BD\\pins_tb.out"
say "B pins, tables: $(tail -1 "$BU/pins_tb.out")"
ps "$T/identity_runs.ps1" -Exe "$BW" -Tag "buildB_c$tag" -Jobs 3 | tail -1 | cut -c1-160
say "identity: $(bash "$T/identity_compare.sh" parent_150374ff "buildB_c$tag" | grep -cE ' IDENTICAL ') sets IDENTICAL, see out/ident/buildB_c$tag/COMPARE.txt"
grep -vE ' IDENTICAL ' "$J/out/ident/buildB_c$tag/COMPARE.txt" | cut -c1-200 >> "$O"
F12="$W\\out\\exp\\fens_12k_v2.txt"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\warm_identity.py $PARENT_EXE $BW $F12 $W\\out\\ident\\warm_c${tag}_nt --n 2000 --nodes 20000" -Log "$W\\out\\ident\\warm_c${tag}_nt.log"
say "warm identity, no tables, exit $?: $(tail -1 "$J/out/ident/warm_c${tag}_nt.log" | cut -c1-200)"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\warm_identity.py $PARENT_EXE $BW $F12 $W\\out\\ident\\warm_c${tag}_tb --n 2000 --nodes 20000 --tables D:\\syzygy345" -Log "$W\\out\\ident\\warm_c${tag}_tb.log"
say "warm identity, tables, 12k FENs, exit $?: $(tail -1 "$J/out/ident/warm_c${tag}_tb.log" | cut -c1-200)"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\warm_identity.py $PARENT_EXE $BW $W\\out\\exp\\root\\clock.fens $W\\out\\ident\\warm_c${tag}_tbclock --n 2000 --nodes 20000 --tables D:\\syzygy345" -Log "$W\\out\\ident\\warm_c${tag}_tbclock.log"
say "warm identity, tables, clock fixture, exit $?: $(tail -1 "$J/out/ident/warm_c${tag}_tbclock.log" | cut -c1-200)"
# bench signature per option value
mkdir -p "$BU/sig"
for o in "SyzygyTbBounds=1" "SyzygyTbBounds=2" "SyzygyTbBounds=4" "SyzygyTbBounds=7" "SyzygyRootExact=1" "SyzygyRootExact=2" "SyzygyRootExact=3" "SyzygyRule50=1" "SyzygyRule50=2" "SyzygyRule50=3" "SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3"; do
  n=$(echo "$o" | tr ' =' '__')
  a=""; for x in $o; do a="$a --opt $x"; done
  ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\sig\\${n}_nt.json --expect none --depths 11,13,16,20,22 --no-net-off $a" -Log "$BD\\sig\\${n}_nt.out"
  ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\sig\\${n}_tb.json --expect none --depths 11,13,16,20,22 --no-net-off --tables D:\\syzygy345 $a" -Log "$BD\\sig\\${n}_tb.out"
  say "sig [$o] no tables: $(python -I -B -c "import json,sys; print(' '.join(str(v) for v in json.load(open(sys.argv[1]))['on'].values()))" "$BD\\sig\\${n}_nt.json") | tables: $(python -I -B -c "import json,sys; print(' '.join(str(v) for v in json.load(open(sys.argv[1]))['on'].values()))" "$BD\\sig\\${n}_tb.json")"
done
say "end $(date)"
