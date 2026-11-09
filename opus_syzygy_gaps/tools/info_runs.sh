#!/usr/bin/env bash
# info_runs.sh <tag> <claims exe tag> - information for QA, no verdict, no games. Plain engine out/exe/cand_<tag>_plain.exe, parent out/exe/p6_plain.exe. Output out/qual/info_<tag>/SUMMARY.txt.
#   1 warm table at clock 0, then the same FEN at a later clock: claims and the moves played, parent against all switches on, judged by the exact solver rows (warm_move_check.py).
#   2 per bit, 200,000 roots above the loaded tables, depth 10: claims against Fathom, moves against python-chess (move_quality.py), parent run reused.
#   3 per bit, claim harness: 3000 roots depth 10; 1250 two-plies-back zugzwang roots depth 16.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
tag=$1; claims=$2
O=$J/out/qual/info_$tag; OW="$W\\out\\qual\\info_$tag"
mkdir -p "$O"
S=$O/SUMMARY.txt
ON="--opt SyzygyTbBounds=7 --opt SyzygyRootExact=3 --opt SyzygyRule50=3"
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
say() { echo "$*" >> "$S"; }
say "start $(date) exe sha256 $(sha256sum "$J/out/exe/cand_${tag}_plain.exe" | cut -c1-64)"
pin -Exe "$PY" -ArgLine "-I -B $WT\\warm_claims.py clock $W\\out\\exe\\p6_plain.exe $W\\out\\exp\\warm\\f1.clock.tsv $OW\\warm_parent.jsonl --tables $W\\out\\tb\\man34 --depth 14 --jobs 2" -Log "$OW\\warm_parent.log"
say "warm parent: $(head -1 "$O/warm_parent.log" | cut -c1-220)"
pin -Exe "$PY" -ArgLine "-I -B $WT\\warm_claims.py clock $W\\out\\exe\\cand_${tag}_plain.exe $W\\out\\exp\\warm\\f1.clock.tsv $OW\\warm_on.jsonl --tables $W\\out\\tb\\man34 --depth 14 --jobs 2 $ON" -Log "$OW\\warm_on.log"
say "warm on: $(head -1 "$O/warm_on.log" | cut -c1-220)"
python -I -B "$T/warm_move_check.py" "$J/out/exp/warm/f1.later.exact.jsonl" "parent=$O/warm_parent.jsonl" "on=$O/warm_on.jsonl" 2>&1 | cut -c1-200 >> "$S"
for o in SyzygyTbBounds=1 SyzygyTbBounds=2 SyzygyTbBounds=4 SyzygyRootExact=3 SyzygyRule50=3; do
  n=$(echo "$o" | tr '=' '_')
  pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\cand_${tag}_plain.exe $W\\out\\exp\\e1\\roots200k.fens $OW\\above_$n.jsonl --tables $W\\out\\tb\\man34 --depth 10 --jobs 2 --opt $o" -Log "$OW\\above_$n.log"
  say "$o above: $(head -1 "$O/above_$n.log" | cut -c1-70) claims: $(python -I -B "$T/false_claims.py" "$J/out/exp/e1/roots200k.fens" "$J/out/exp/e1/roots200k.fathom" "$O/above_$n.jsonl" --list "$O/above_$n.false.tsv" | cut -c1-200)"
  say "$o quality: $(python -I -B "$T/move_quality.py" "$J/out/exp/e1/roots200k.oracle.jsonl" "parent=$J/out/qual/p6/above_d10.jsonl" "$n=$O/above_$n.jsonl" --json "$O/quality_$n.json" | tail -1 | cut -c1-200)"
done
for m in 1 2 4 7; do
  say "--- claims mask $m"
  CLAIM_LABEL=info_$tag bash "$T/claims_build_run.sh" "$claims" "SyzygyTbBounds=$m" 2>&1 | grep -E 'roots |wrong [1-9]|correction' | cut -c1-100 >> "$S"
  CLAIM_FENS='exp\zz\zz2roots.fens' CLAIM_FIRST=0 CLAIM_DEPTH=16 CLAIM_LABEL=zz2_$tag bash "$T/claims_build_run.sh" "$claims" "SyzygyTbBounds=$m" 2>&1 | grep -E 'roots |wrong [1-9]' | cut -c1-100 >> "$S"
done
say "end $(date)"
