#!/usr/bin/env bash
# R3-3: identity check + 5-depth prebench pins (runner Bench1 protocol) for every runtime option of one exe.
# usage: run_pins.sh <exe> <out_prefix>
set -u
EXE=$1; OUT=$2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
T=/f/opus_scratch/r3/R3-3/tools
echo "== uci_check --full $(date '+%F %T')"
nice -n 19 $PY -I -B $LA/2_build/uci_check.py "$EXE" --full > "${OUT}_identity.log" 2>&1
echo "uci_check exit $? : $(tail -1 "${OUT}_identity.log")"
echo "== pins $(date '+%F %T')"
nice -n 19 $PY -I -B $T/measure_pins.py "$EXE" "${OUT}_pins.json" \
  --set 'CHP1=CorrHistPlus:1' \
  --set 'CHP2=CorrHistPlus:2' \
  --set 'CHP4=CorrHistPlus:4' \
  --set 'CUCKOO=CuckooRep:true' \
  --set 'SYZ=SyzygyPath:D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345' \
  --set 'HR2=HistRework:2' \
  --set 'CM1=CorrMargins:1' \
  --set 'NS99=NetScale:99' \
  --set 'IT=IntendedThreefold:true' \
  --set 'HD10=HardDeadline:10' \
  --set 'CE1=CorrExt:1' \
  --set 'HR3=HistRework:3' \
  --set 'MKT=MaterialKeyTable:true' \
  --set 'HR1=HistRework:1' \
  --set 'SMPB=SmpBestThread:true' \
  --set 'LTT=LocklessTT:true' \
  --set 'SMPX=SmpExactNodes:true'
echo "pins exit $? $(date '+%F %T')"
