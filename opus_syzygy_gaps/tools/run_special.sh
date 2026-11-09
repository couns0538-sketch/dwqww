#!/usr/bin/env bash
# run_special.sh <tb_root exe tag> <out tag> [Name=Value ...] - run the adversarial root fixtures through a tb_root build and check
# them against the python-chess oracle (computed once per fixture). Rule on for all; rule off for promo and rep as well.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
VPY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
exe=$1; tag=$2
shift 2
D=$J/out/exp/special
for kind in promo ep rep castle clock100; do
  if [ ! -e "$D/s1.$kind.oracle.jsonl" ]; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$VPY" \
      -ArgLine "-I -B $W\\repo\\opus_syzygy_gaps\\tools\\oracle_chess.py D:\\syzygy345 $W\\out\\exp\\special\\s1.$kind.fens $W\\out\\exp\\special\\s1.$kind.oracle.jsonl" \
      -Log "$W\\out\\exp\\special\\s1.$kind.oracle.log"
  fi
  for rule in 1 0; do
    if [ "$rule" = 0 ] && [ "$kind" != promo ] && [ "$kind" != rep ]; then continue; fi
    B=${tag}_${kind}_r$rule
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$W\\out\\exe\\tb_root_$exe.exe" \
      -ArgLine "D:\\syzygy345 $W\\out\\exp\\special\\s1.$kind.fens $rule $*" \
      -OutFile "$W\\out\\exp\\special\\$B.out" -ErrFile "$W\\out\\exp\\special\\$B.err"
    printf '%s: ' "$B"
    python -I -B "$T/root_check.py" "$D/s1.$kind.oracle.jsonl" "$D/$B.out" --rule50 "$rule" --json "$D/$B.check.json" --list "$D/$B.bad.tsv"
  done
done
