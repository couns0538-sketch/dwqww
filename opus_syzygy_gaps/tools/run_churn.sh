#!/usr/bin/env bash
# run_churn.sh <san tag> <plain exe name> [ops] [seed base] - uci_churn.py on the plain engine, the UBSan engine and the ASan engine, Threads 1 and 2, and tb_root under ASan on the missing-child boundary roots.
# Output out/exp/hunt/churn_<tag>/. A summary line per run in SUMMARY.txt. Exits by itself.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
VPY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
tag=$1; plain=$2; ops=${3:-3000}; seed=${4:-100}
O=$J/out/exp/hunt/churn_$tag; OW="$W\\out\\exp\\hunt\\churn_$tag"
mkdir -p "$O"
S=$O/SUMMARY.txt
X="$W\\out\\exp"
POOL="$X\\exact\\b1.boundary.fens,$X\\root\\clock.fens,$X\\special\\s1.promo.fens,$X\\special\\s1.ep.fens,$X\\special\\s1.castle.fens,$X\\special\\s1.clock100.fens,$X\\special2\\up.fens,$X\\e1\\roots200k.fens,$X\\fens_12k_v2.txt"
TB="D:\\syzygy345,$W\\out\\tb\\man34,$W\\out\\tb\\nochild,$W\\out\\tb\\nodtz,$W\\out\\tb\\rejected,$W\\out\\tb\\wdl_only,$W\\out\\tb\\dtzonly"
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
pa() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned_asan.ps1" -Tag "$tag" "$@"; }
one() { # name runner exe threads seed bench
  n=$1; r=$2; e=$3; th=$4; sd=$5; b=$6
  $r -Exe "$VPY" -ArgLine "-I -B $WT\\uci_churn.py $e $OW\\$n.json --seed $sd --ops $ops --pool $POOL --tables $TB --threads $th --bench-expect $b --limit-s 300" -Log "$OW\\$n.log"
  echo "$n exit $? $(tail -1 "$O/$n.log" | cut -c1-260)" >> "$S"
}
one plain_t1 pin "$W\\out\\exe\\$plain.exe" 1 $seed 862329
one ubsan_t1 pin "$W\\out\\san\\$tag\\forge_ubsan.exe" 1 $((seed+1)) 862329
one asan_t1 pa "$W\\out\\san\\$tag\\forge_asan.exe" 1 $((seed+2)) 819221
one plain_t2 pin "$W\\out\\exe\\$plain.exe" 2 $((seed+3)) 862329
one asan_t2 pa "$W\\out\\san\\$tag\\forge_asan.exe" 2 $((seed+4)) 819221
for d in nochild nodtz rejected wdl_only; do
  pa -Heap -Exe "$W\\out\\san\\$tag\\tb_root_asan.exe" -ArgLine "$W\\out\\tb\\$d $W\\out\\exp\\hunt\\kqkr_b.fens 1 SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3" -OutFile "$OW\\missing_asan_$d.out" -ErrFile "$OW\\missing_asan_$d.err"
  echo "missing child asan heap $d exit $? rows $(wc -l < "$O/missing_asan_$d.out") $(tail -1 "$O/missing_asan_$d.err" | cut -c1-90)" >> "$S"
done
echo "end $(date)" >> "$S"
cut -c1-200 "$S"
