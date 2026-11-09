#!/usr/bin/env bash
# qual_all.sh <tag> <engine exe name in out/exe> <tb_root exe tag> <tb_claims exe tag> [Name=Value ...] - the fixture suite for one engine + option set, all under pinned.ps1,
# results in out/qual/<tag>/, a table in out/qual/<tag>/SUMMARY.txt. Steps can be chosen with QUAL_STEPS (default all); a finished step output is not recomputed.
# Parent run: pass no options; steps that need candidate options simply run without them. Nothing here is a game.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
VPY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
tag=$1; exe=$2; rootexe=$3; claimexe=$4
shift 4
OPTS=("$@")
OPTARGS=""; for o in "${OPTS[@]}"; do OPTARGS="$OPTARGS --opt $o"; done
Q=$J/out/qual/$tag; QW="$W\\out\\qual\\$tag"
mkdir -p "$Q"
S=$Q/SUMMARY.txt
STEPS=${QUAL_STEPS:-root uci warm toggle claims playout misc quality}
JOBS=${QUAL_JOBS:-4}
say() { echo "$*" >> "$S"; }
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
say "=== $tag exe $exe root $rootexe claims $claimexe opts [${OPTS[*]-}] steps [$STEPS]"
say "exe sha256 $(sha256sum "$J/out/exe/$exe.exe" | cut -c1-64)"
EX=$J/out/exp/exact/b2500.exact.jsonl

for step in $STEPS; do
case $step in
root)
  # root path: exact boundary oracle; all clock and special fixtures against the python-chess rule (rule on; rule off on promo and rep)
  for fx in "exact\\b1.boundary.fens|exp/exact/b2500.exact.jsonl|boundary" ; do
    IFS='|' read -r f o n <<< "$fx"
    if [ ! -e "$Q/root_$n.out" ]; then pin -Exe "$W\\out\\exe\\tb_root_$rootexe.exe" -ArgLine "D:\\syzygy345 $W\\out\\exp\\$f 1 ${OPTS[*]-}" -OutFile "$QW\\root_$n.out" -ErrFile "$QW\\root_$n.err"; fi
    say "root_$n exact: $(python -I -B "$T/exact_check.py" "$J/out/$o" --root "$Q/root_$n.out" --json "$Q/root_$n.json" --list "$Q/root_$n.bad.tsv")"
  done
  for k in clock promo ep rep castle clock100; do
    if [ "$k" = clock ]; then f="root\\clock.fens"; o=exp/root/clock.oracle.jsonl; else f="special\\s1.$k.fens"; o=exp/special/s1.$k.oracle.jsonl; fi
    if [ ! -e "$Q/rootc_$k.out" ]; then pin -Exe "$W\\out\\exe\\tb_root_$rootexe.exe" -ArgLine "D:\\syzygy345 $W\\out\\exp\\$f 1 ${OPTS[*]-}" -OutFile "$QW\\rootc_$k.out" -ErrFile "$QW\\rootc_$k.err"; fi
    say "rootc_$k table rule: $(python -I -B "$T/root_check.py" "$J/out/$o" "$Q/rootc_$k.out" --json "$Q/rootc_$k.json" --list "$Q/rootc_$k.bad.tsv")"
  done
  for k in promo rep; do
    if [ ! -e "$Q/rootc0_$k.out" ]; then pin -Exe "$W\\out\\exe\\tb_root_$rootexe.exe" -ArgLine "D:\\syzygy345 $W\\out\\exp\\special\\s1.$k.fens 0 ${OPTS[*]-}" -OutFile "$QW\\rootc0_$k.out" -ErrFile "$QW\\rootc0_$k.err"; fi
    say "rootc0_$k rule off: $(python -I -B "$T/root_check.py" "$J/out/exp/special/s1.$k.oracle.jsonl" "$Q/rootc0_$k.out" --rule50 0 2>&1 | tail -1)"
  done
  ;;
uci)
  # the engine itself: bestmove and score on the boundary and on the other root fixtures
  if [ ! -e "$Q/uci_boundary.jsonl" ]; then pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\$exe.exe $W\\out\\exp\\exact\\b1.boundary.fens $QW\\uci_boundary.jsonl --tables D:\\syzygy345 --depth 8 --jobs $JOBS $OPTARGS" -Log "$QW\\uci_boundary.log"; fi
  say "uci_boundary log: $(head -1 "$Q/uci_boundary.log" | cut -c1-60)"
  say "uci_boundary exact: $(python -I -B "$T/exact_check.py" "$EX" --run "$Q/uci_boundary.jsonl" --json "$Q/uci_boundary.json" --list "$Q/uci_boundary.bad.tsv")"
  say "uci_boundary mates: $("/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe" -I -B "$T/mate_pv_check.py" "$Q/uci_boundary.jsonl" 2>&1 | head -1)"
  for k in clock promo ep clock100; do
    if [ "$k" = clock ]; then f="root\\clock.fens"; o=exp/root/clock.oracle.jsonl; r=rootc_clock; else f="special\\s1.$k.fens"; o=exp/special/s1.$k.oracle.jsonl; r=rootc_$k; fi
    if [ ! -e "$Q/uci_$k.jsonl" ]; then pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\$exe.exe $W\\out\\exp\\$f $QW\\uci_$k.jsonl --tables D:\\syzygy345 --depth 6 --jobs $JOBS $OPTARGS" -Log "$QW\\uci_$k.log"; fi
    say "uci_$k table rule: $(python -I -B "$T/root_move_check.py" "$J/out/$o" "$Q/uci_$k.jsonl" --ranks "$Q/$r.out" --json "$Q/uci_$k.json" --list "$Q/uci_$k.bad.tsv")"
  done
  ;;
warm)
  if [ ! -e "$Q/warm_clock.jsonl" ]; then pin -Exe "$PY" -ArgLine "-I -B $WT\\warm_claims.py clock $W\\out\\exe\\$exe.exe $W\\out\\exp\\warm\\f1.clock.tsv $QW\\warm_clock.jsonl --tables $W\\out\\tb\\man34 --depth 14 --jobs $JOBS $OPTARGS" -Log "$QW\\warm_clock.log"; fi
  say "warm_clock: $(head -1 "$Q/warm_clock.log" | cut -c1-200)"
  ;;
toggle)
  if [ ! -e "$Q/toggle.jsonl" ]; then pin -Exe "$PY" -ArgLine "-I -B $WT\\warm_claims.py toggle $W\\out\\exe\\$exe.exe $W\\out\\exp\\warm\\f1.toggle.fens $QW\\toggle.jsonl --tables D:\\syzygy345 --depth 10 --jobs $JOBS $OPTARGS" -Log "$QW\\toggle.log"; fi
  say "toggle: $(head -1 "$Q/toggle.log" | cut -c1-200)"
  ;;
claims)
  C=$T/claims_build_run.sh
  say "--- claims"
  CLAIM_LABEL=q$tag bash "$C" "$claimexe" "${OPTS[@]}" 2>&1 | grep -E 'roots |wrong [1-9]|correction' | cut -c1-100 >> "$S"
  CLAIM_FENS='exp\root\clock.fens' CLAIM_FIRST=0 CLAIM_LABEL=clock_q$tag bash "$C" "$claimexe" "${OPTS[@]}" 2>&1 | grep -E 'roots |wrong [1-9]|correction' | cut -c1-100 >> "$S"
  CLAIM_WARM=1 CLAIM_FENS='exp\warm\f1.clock.tsv' CLAIM_FIRST=0 CLAIM_DEPTH=12 CLAIM_LABEL=warm_q$tag bash "$C" "$claimexe" "${OPTS[@]}" 2>&1 | grep -E 'roots |wrong [1-9]' | cut -c1-100 >> "$S"
  CLAIM_FENS='exp\zz\zz_pred.fens' CLAIM_FIRST=0 CLAIM_DEPTH=16 CLAIM_LABEL=zz_q$tag bash "$C" "$claimexe" "${OPTS[@]}" 2>&1 | grep -E 'roots |wrong [1-9]' | cut -c1-100 >> "$S"
  ;;
playout)
  if [ ! -e "$Q/playout.jsonl" ]; then pin -Exe "$VPY" -ArgLine "-I -B $WT\\playout_check.py $W\\out\\exe\\$exe.exe D:\\syzygy345 $W\\out\\exp\\exact\\b2500.exact.jsonl $QW\\playout.jsonl --depth 6 --first ${QUAL_PLAYOUT:-800} --jobs $JOBS $OPTARGS" -Log "$QW\\playout.log"; fi
  say "playout: $(head -1 "$Q/playout.log" | cut -c1-260)"
  ;;
misc)
  if [ ! -e "$Q/misc.json" ]; then pin -Exe "$VPY" -ArgLine "-I -B $WT\\uci_misc_checks.py $W\\out\\exe\\$exe.exe D:\\syzygy345 $W\\out\\exp\\exact\\b2500.exact.jsonl $W\\out\\exp\\special\\s1.castle.fens $W\\out\\exp\\e1\\roots5.fens $QW\\misc.json $OPTARGS" -Log "$QW\\misc.log"; fi
  say "misc: $(head -1 "$Q/misc.log" | cut -c1-300)"
  ;;
quality)
  # 5-man roots above the 3-4 piece tables: root claims against Fathom, move result against python-chess
  if [ ! -e "$Q/above_d10.jsonl" ]; then pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\$exe.exe $W\\out\\exp\\e1\\roots200k.fens $QW\\above_d10.jsonl --tables $W\\out\\tb\\man34 --depth 10 --jobs $JOBS $OPTARGS" -Log "$QW\\above_d10.log"; fi
  say "above_d10 log: $(head -1 "$Q/above_d10.log" | cut -c1-60)"
  say "above_d10 claims: $(python -I -B "$T/false_claims.py" "$J/out/exp/e1/roots200k.fens" "$J/out/exp/e1/roots200k.fathom" "$Q/above_d10.jsonl" --json "$Q/above_d10.claims.json" --list "$Q/above_d10.false.tsv")"
  say "above_d10 mates: $("/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe" -I -B "$T/mate_pv_check.py" "$Q/above_d10.jsonl" 2>&1 | head -1)"
  ;;
esac
done
say "=== end $tag"
