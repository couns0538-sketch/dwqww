#!/usr/bin/env bash
# after_w6.sh <new tag> <frozen tag> - the after_w6 line: trial_w6 source + P6 port = its parent; + this job's patch for that line = candidate. Builds with the kit recipe and the six trial_w6 defines:
#   parent (port on w6), Build A' (macros off, must equal that parent byte for byte), Build B' (macros on, options 0), pins of B' without and with tables, identity of B' against the parent.
# The merge: patches/syzygy_gaps_after_w6p6.patch has the changed lines of syzygy_gaps_after_p6.patch in the same order (checked here). One hunk needed new context: trial_w6 wraps the store line between
#   its two insertions in #if FORGE_SPD_TT_NOTLS. Speed switches at 0, after preprocessing: macros off = the P6 tree, macros on = the frozen candidate. No changed line inside a speed conditional (w6_arm_check.py).
# All options on: B' must search the nodes of the frozen P6-line Build B, since the speed switches are node-identical: bench, 30000 roots above the tables, all root fixtures, boundary roots, warm rows.
# UBSan with the six defines and all options on. ASan is not run on this line (MSVC build has no AVX-512 / PEXT variant of these switches).
# Writes patches/syzygy_port_and_gaps_after_w6.patch and out/builds/after_w6_<new tag>.txt, and checks that this one patch on a fresh trial_w6 tree gives the same tree.
# The w6 exe itself is compared by pins (the port adds options, so no byte identity with it). Any failed check: the last line says so and the exit code is 1.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
R=$J/repo/opus_syzygy_gaps
T=$R/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
tag=$1; ftag=$2
SP='FORGE_SPD_TT_NOTLS=1,FORGE_SPD_NO_ZERO_MOVELISTS=2,FORGE_SEARCH_SPEED2=1,FORGE_SPD_PREFETCH_EARLY=1,FORGE_SPD_SLIDER_PEXT=1,FORGE_SPD_NNUE_ZMM=1'
ALL='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
ON='SyzygyTbBounds=7;SyzygyRootExact=3;SyzygyRule50=3'
ONA='--opt SyzygyTbBounds=7 --opt SyzygyRootExact=3 --opt SyzygyRule50=3'
ONS='SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3'
O=$J/out/builds/after_w6_$tag.txt
SRC=$J/out/src
P6=$R/patches/syzygy_gaps_after_p6.patch
P=$R/patches/syzygy_gaps_after_w6p6.patch
PW6=$R/patches/syzygy_port_and_gaps_after_w6.patch
fails=0
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
say() { echo "$*" | tee -a "$O" | cut -c1-200; }
# need <text that must be in the result> <label> <result>
need() { say "$2: $3"; case "$3" in *"$1"*) ;; *) fails=$((fails + 1)); say "FAILED CHECK: $2";; esac; }
same() { need '"verdict": "IDENTICAL"' "$1" "$(python -I -B "$T/compare_runs.py" "$2" "$3" | cut -c1-300)"; }
sig() { python -I -B -c "import json,sys; print(' '.join(str(v) for v in json.load(open(sys.argv[1]))['on'].values()))" "$1"; }
lines() { grep -E '^[+-]' "$1" | grep -vE '^(\+\+\+|---) '; }

TREE=w6p6g_$tag
[ -e "$SRC/$TREE" ] && { echo "refusing: $SRC/$TREE exists"; exit 2; }
say "start $(date) gaps patch $(md5sum "$P" | cut -c1-32) P6-line patch $(md5sum "$P6" | cut -c1-32)"
lines "$P6" > "$O.lines_p6"; lines "$P" > "$O.lines_w6"
cmp -s "$O.lines_p6" "$O.lines_w6" || { say "FAIL the two gaps patches change different lines"; exit 1; }
say "same $(wc -l < "$O.lines_p6") changed lines, same order, in both gaps patches"
mkdir -p "$SRC/$TREE"
tar -x -C "$SRC/$TREE" -f "$SRC/lock_d4f4312.tar"
( cd "$SRC/$TREE" && patch -p1 -F0 --no-backup-if-mismatch < ../trial_w6.patch > /dev/null && patch -p1 -F0 --no-backup-if-mismatch < "$J/repo/opus_r13/p6/syzygy_port.patch" > /dev/null \
  && git init -q . && git config core.autocrlf false && git config user.name couns0538-sketch && git config user.email couns0538@gmail.com && git add -A && git commit -q -m "w6 + port" ) || { say "FAIL w6 + port"; exit 1; }
PARENT="$W\\out\\src\\$TREE"
say "parent tree $TREE w6 + port, head $(git -C "$SRC/$TREE" log -1 --format=%h), trial_w6.patch md5 $(md5sum "$SRC/trial_w6.patch" | cut -c1-32)"
ps "$T/kit_build.ps1" -SrcDir "$PARENT" -Tag "w6p6_parent_$tag" -Defines "$SP" | tail -1 | cut -c1-160
PSHA=$(sha256sum "$J/out/builds/w6p6_parent_$tag/forge_w6p6_parent_$tag.exe" | cut -c1-64 | tr a-z A-Z)
say "parent sha256 $PSHA"
# no pipe on patch: a rejected hunk must stop the line (R3 finding 8)
( cd "$SRC/$TREE" && patch -p1 -F0 --no-backup-if-mismatch < "$P" > "$O.patch.log" ) || { say "FAIL gaps patch rejected, see $O.patch.log"; exit 1; }
if find "$SRC/$TREE" -name '*.rej' | grep -q .; then say "FAIL rejected hunks"; exit 1; fi
( cd "$SRC/$TREE" && git add -A && git commit -q -m "gaps" ) || { say "FAIL commit"; exit 1; }
say "gaps applied with -F0, head $(git -C "$SRC/$TREE" log -1 --format=%h)"
need 'ALL EQUAL' "preprocess, speed switches 0, macros off, against the P6 tree" "$(ps "$T/preprocess_diff.ps1" -Parent "$W\\out\\src\\p6_port" -Cand "$PARENT" | tail -1)"
need 'ALL EQUAL' "preprocess, speed switches 0, macros on, against the frozen candidate" "$(ps "$T/preprocess_diff.ps1" -Parent "$W\\out\\src\\cand" -Cand "$PARENT" -Defines "$ALL" | tail -1)"
python -I -B "$T/w6_arm_check.py" "$P6" "$PARENT" > "$O.arms" 2>&1
need 'CLEAN' "changed lines against speed conditionals" "$(tail -1 "$O.arms")"
need 'IDENTITY PASS' "A'" "$(ps "$T/kit_build.ps1" -SrcDir "$PARENT" -Tag "w6p6_A_$tag" -Defines "$SP" -WantSha "$PSHA" | tail -1)"
ps "$T/kit_build.ps1" -SrcDir "$PARENT" -Tag "w6p6_B_$tag" -Defines "$SP,$ALL" | tail -1 | cut -c1-160
BX="$J/out/builds/w6p6_B_$tag/forge_w6p6_B_$tag.exe"
say "B' sha256 $(sha256sum "$BX" | cut -c1-64)"
BW="$W\\out\\builds\\w6p6_B_$tag\\forge_w6p6_B_$tag.exe"
BD="$W\\out\\builds\\w6p6_B_$tag"
BU="$J/out/builds/w6p6_B_$tag"
PW="$W\\out\\builds\\w6p6_parent_$tag\\forge_w6p6_parent_$tag.exe"
FB="$W\\out\\builds\\buildB_c${ftag}_pc1\\forge_buildB_c${ftag}_pc1.exe"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\pins_off.json --expect lock" -Log "$BD\\pins_off.out"
need 'PINS ALL EQUAL' "B' pins off" "$(tail -1 "$BU/pins_off.out")"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\pins_tb.json --expect p6path --tables D:\\syzygy345 --no-net-off" -Log "$BD\\pins_tb.out"
need 'PINS ALL EQUAL' "B' pins tables" "$(tail -1 "$BU/pins_tb.out")"
ps "$T/identity_runs.ps1" -Exe "$PW" -Tag "w6p6_parent_$tag" -Sets 'net_on,tb_roots,tb_clock' -Jobs 3 > /dev/null
ps "$T/identity_runs.ps1" -Exe "$BW" -Tag "w6p6_B_$tag" -Sets 'net_on,tb_roots,tb_clock' -Jobs 3 > /dev/null
for s in net_on tb_roots tb_clock; do same "$s, options 0, against the w6 + port parent" "$J/out/ident/w6p6_parent_$tag/$s.jsonl" "$J/out/ident/w6p6_B_$tag/$s.jsonl"; done
# the speed switches must not change a node
for s in net_on tb_roots tb_clock; do same "$s, options 0, against the P6 parent 150374ff" "$J/out/ident/parent_150374ff/$s.jsonl" "$J/out/ident/w6p6_B_$tag/$s.jsonl"; done
# all options on: the same nodes as the frozen P6-line Build B, so the suite's results carry over to this line
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\pins_on_nt.json --expect lock $ONA" -Log "$BD\\pins_on_nt.out"
need 'PINS ALL EQUAL' "B' all on, no tables, against the lock pins" "$(tail -1 "$BU/pins_on_nt.out")"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $BW $BD\\pins_on_tb.json --expect none --depths 11,13,16,20,22 --no-net-off --tables D:\\syzygy345 $ONA" -Log "$BD\\pins_on_tb.out"
A=$(sig "$BD\\pins_on_tb.json"); F=$(sig "$W\\out\\builds\\buildB_c${ftag}_pc1\\sig\\SyzygyTbBounds_7_SyzygyRootExact_3_SyzygyRule50_3_tb.json")
need "$F" "B' all on, tables, bench [frozen P6 line: $F]" "$A"
ps "$T/identity_runs.ps1" -Exe "$FB" -Tag "on_buildB_c$ftag" -Sets 'tb_roots,tb_clock,tb_special' -Opt "$ON" -Jobs 3 > /dev/null
ps "$T/identity_runs.ps1" -Exe "$BW" -Tag "on_w6p6_B_$tag" -Sets 'tb_roots,tb_clock,tb_special' -Opt "$ON" -Jobs 3 > /dev/null
for s in tb_roots tb_clock tb_promo tb_ep tb_rep tb_castle tb_clock100; do same "$s, all on, against the frozen P6 line" "$J/out/ident/on_buildB_c$ftag/$s.jsonl" "$J/out/ident/on_w6p6_B_$tag/$s.jsonl"; done
F8="$W\\out\\exp\\exact\\b1.boundary.fens"
for e in "$FB|on_buildB_c$ftag" "$BW|on_w6p6_B_$tag"; do
  x=${e%|*}; n=${e#*|}
  [ -e "$J/out/ident/$n/boundary.jsonl" ] || ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $x $F8 $W\\out\\ident\\$n\\boundary.jsonl --jobs 3 --depth 8 --tables D:\\syzygy345 $ONA" -Log "$W\\out\\ident\\$n\\boundary.log"
done
same "boundary roots depth 8, all on, against the frozen P6 line" "$J/out/ident/on_buildB_c$ftag/boundary.jsonl" "$J/out/ident/on_w6p6_B_$tag/boundary.jsonl"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\warm_identity.py $FB $BW $W\\out\\exp\\root\\clock.fens $W\\out\\ident\\warm_on_w6_$tag --n 2000 --nodes 20000 --tables D:\\syzygy345 $ONA" -Log "$W\\out\\ident\\warm_on_w6_$tag.log"
need 'IDENTICAL' "warm rows, tables, clock fixture, all on, against the frozen P6 line" "$(tail -1 "$J/out/ident/warm_on_w6_$tag.log" | cut -c1-200)"
# UBSan with the six defines, all on
ps "$T/sanitize_builds.ps1" -Src "$PARENT" -Tag "w6_$tag" -Defines "$SP,$ALL" -SkipAsan | tail -1 | cut -c1-160
SD="$W\\out\\san\\w6_$tag"
SU="$J/out/san/w6_$tag"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\pins.py $SD\\forge_ubsan.exe $SD\\pins.json --expect none --depths 13 --no-net-off $ONA" -Log "$SD\\pins.out"
need 862329 "UBSan, all on, no tables, bench 13" "exit $? $(sig "$SD\\pins.json")"
ps "$T/pinned.ps1" -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $SD\\forge_ubsan.exe $F8 $SD\\boundary.jsonl --jobs 2 --depth 8 --tables D:\\syzygy345 $ONA" -Log "$SD\\boundary.log"
need 'exit 0' "UBSan, all on, boundary roots" "exit $?"
same "UBSan rows against the kit build's rows" "$J/out/ident/on_w6p6_B_$tag/boundary.jsonl" "$SU/boundary.jsonl"
ps "$T/pinned.ps1" -Exe "$SD\\tb_root_ubsan.exe" -ArgLine "D:\\syzygy345 $W\\out\\exp\\root\\clock.fens 1 $ONS" -OutFile "$SD\\root_clock.out" -ErrFile "$SD\\root_clock.err"
need 'exit 0' "UBSan, tb_root, clock fixture" "exit $? rows $(wc -l < "$SU/root_clock.out")"
# the one patch for the crew
mkdir -p "$SRC/w6_only_$tag"; tar -x -C "$SRC/w6_only_$tag" -f "$SRC/lock_d4f4312.tar"; ( cd "$SRC/w6_only_$tag" && patch -p1 -F0 --no-backup-if-mismatch < ../trial_w6.patch > /dev/null )
( cd "$SRC" && diff -ruN --strip-trailing-cr "w6_only_$tag/include" "$TREE/include"; diff -ruN --strip-trailing-cr "w6_only_$tag/src" "$TREE/src" ) > "$PW6"
say "after_w6 patch lines $(wc -l < "$PW6") md5 $(md5sum "$PW6" | cut -c1-32) sha256 $(sha256sum "$PW6" | cut -c1-64)"
mkdir -p "$SRC/w6_check_$tag"; tar -x -C "$SRC/w6_check_$tag" -f "$SRC/lock_d4f4312.tar"
( cd "$SRC/w6_check_$tag" && patch -p1 -F0 --no-backup-if-mismatch < ../trial_w6.patch > /dev/null && patch -p1 -F0 --no-backup-if-mismatch < "$PW6" > /dev/null )
need 'SAME TREE' "after_w6 patch on a fresh trial_w6 tree" "$(diff -r --strip-trailing-cr "$SRC/w6_check_$tag/src" "$SRC/$TREE/src" > /dev/null && diff -r --strip-trailing-cr "$SRC/w6_check_$tag/include" "$SRC/$TREE/include" > /dev/null && echo SAME TREE || echo DIFFERENT)"
say "end $(date) failed checks $fails"
[ "$fails" -eq 0 ] && say "VERDICT after_w6 line: ALL CHECKS PASS" || say "VERDICT after_w6 line: $fails CHECKS FAILED"
[ "$fails" -eq 0 ]
