#!/usr/bin/env bash
# special2.sh <tag> <engine exe name> <tb_root exe tag> [Name=Value ...] - second set of adversarial root fixtures, judged by oracle_exact.py rows (no engine flag):
#   rep2: lines with a live root and a third-occurrence child (7-ply lines), drawn roots (8-ply), shorter lines. up: underpromotion is the only best class.
#   clock0 on WDL-only tables: report at counter 0 (R1 finding 4).
# The fixture files and oracle rows are computed once by special2_prepare (first call). Output: out/qual/<tag>/special2.txt
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
VPY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
tag=$1; exe=$2; root=$3
shift 3
OPTS=("$@")
OPTARGS=""; for o in "${OPTS[@]}"; do OPTARGS="$OPTARGS --opt $o"; done
Q=$J/out/qual/$tag; QW="$W\\out\\qual\\$tag"
D=$J/out/exp/special2; DW="$W\\out\\exp\\special2"
mkdir -p "$Q" "$D"
S=$Q/special2.txt
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
if [ ! -e "$D/s2.rep.fens" ]; then
  pin -Exe "$VPY" -ArgLine "-I -B $WT\\gen_special_fixtures.py D:\\syzygy345 $DW\\s2 --seed 22 --n 3000" -Log "$DW\\gen.log"
fi
if [ ! -e "$D/up.fens" ]; then
  pin -Exe "$VPY" -ArgLine "-I -B $WT\\gen_underpromo.py D:\\syzygy345 $DW\\up.fens --want 300 --tries 2000000" -Log "$DW\\up.log"
fi
cp -n "$J/out/exp/exact/b1.clock0.fens" "$D/clock0.fens"
for k in s2.rep up clock0; do
  if [ ! -e "$D/$k.exact.jsonl" ]; then
    pin -Exe "$VPY" -ArgLine "-I -B $WT\\oracle_exact.py D:\\syzygy345 $DW\\$k.fens $DW\\$k.exact.jsonl --max-seconds-per-root 8" -Log "$DW\\$k.exact.log"
  fi
done
echo "=== $tag $exe root $root opts [${OPTS[*]-}] $(cut -c1-100 "$D/up.log")" >> "$S"
for k in s2.rep up; do
  pin -Exe "$W\\out\\exe\\tb_root_$root.exe" -ArgLine "D:\\syzygy345 $DW\\$k.fens 1 ${OPTS[*]-}" -OutFile "$QW\\sp2_$k.out" -ErrFile "$QW\\sp2_$k.err"
  echo "$k root: $(python -I -B "$T/exact_check.py" "$D/$k.exact.jsonl" --root "$Q/sp2_$k.out" --list "$Q/sp2_$k.bad.tsv")" >> "$S"
  if [ ! -e "$Q/sp2_$k.jsonl" ]; then pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\$exe.exe $DW\\$k.fens $QW\\sp2_$k.jsonl --tables D:\\syzygy345 --depth 6 --jobs ${QUAL_JOBS:-3} $OPTARGS" -Log "$QW\\sp2_$k.log"; fi
  echo "$k uci: $(python -I -B "$T/exact_check.py" "$D/$k.exact.jsonl" --run "$Q/sp2_$k.jsonl" --list "$Q/sp2_$k.uci.bad.tsv")" >> "$S"
done
pin -Exe "$W\\out\\exe\\tb_root_$root.exe" -ArgLine "$W\\out\\tb\\wdl_only $DW\\clock0.fens 1 ${OPTS[*]-}" -OutFile "$QW\\sp2_clock0_wdl.out" -ErrFile "$QW\\sp2_clock0_wdl.err"
echo "clock0 WDL-only root: $(python -I -B "$T/exact_check.py" "$D/clock0.exact.jsonl" --root "$Q/sp2_clock0_wdl.out" --wdl-only --list "$Q/sp2_clock0_wdl.bad.tsv")" >> "$S"
pin -Exe "$W\\out\\exe\\tb_root_$root.exe" -ArgLine "$W\\out\\tb\\wdl_only $W\\out\\exp\\root\\clock.fens 1 ${OPTS[*]-}" -OutFile "$QW\\sp2_clock_wdl.out" -ErrFile "$QW\\sp2_clock_wdl.err"
echo "clock WDL-only root: $(python -I -B "$T/root_check.py" "$J/out/exp/root/clock.oracle.jsonl" "$Q/sp2_clock_wdl.out" --list "$Q/sp2_clock_wdl.bad.tsv")" >> "$S"
echo "   false TB shown: $(grep -cE 'display -?31870' "$Q/sp2_clock_wdl.bad.tsv")" >> "$S"
pin -Exe "$W\\out\\exe\\tb_root_$root.exe" -ArgLine "D:\\syzygy345 $W\\out\\exp\\root\\clock.fens 0 ${OPTS[*]-}" -OutFile "$QW\\sp2_clock_r0.out" -ErrFile "$QW\\sp2_clock_r0.err"
echo "clock rule off root: $(python -I -B "$T/root_check.py" "$J/out/exp/root/clock.oracle.jsonl" "$Q/sp2_clock_r0.out" --rule50 0 --list "$Q/sp2_clock_r0.bad.tsv")" >> "$S"
cut -c1-250 "$S"
