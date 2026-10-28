#!/usr/bin/env bash
# R3-3: spot-check the prebench pins of every entry on the main session's FINAL exes (read-only use of the exes),
# d11/d13 with the runner's Bench1 protocol. usage: spot_check_final.sh <exe_dir> <out_dir>
set -u
X=$1; O=$2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=/f/opus_scratch/r3/R3-3/tools
mkdir -p "$O"
nice -n 19 $PY -I -B $T/measure_pins.py "$X/forge_r3_stack.exe" "$O/final_stack_pins.json" --depths 11,13 \
  --set 'CHP1=CorrHistPlus:1' --set 'CHP2=CorrHistPlus:2' --set 'CHP4=CorrHistPlus:4' --set 'CUCKOO=CuckooRep:true' \
  --set 'SYZ=SyzygyPath:D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345' --set 'HR2=HistRework:2' --set 'CM1=CorrMargins:1' \
  --set 'NS99=NetScale:99' --set 'IT=IntendedThreefold:true' --set 'HD10=HardDeadline:10' --set 'CE1=CorrExt:1' \
  --set 'HR3=HistRework:3' --set 'MKT=MaterialKeyTable:true' --set 'HR1=HistRework:1' --set 'SMPB=SmpBestThread:true' \
  --set 'LTT=LocklessTT:true' --set 'SMPX=SmpExactNodes:true'
nice -n 19 $PY -I -B $T/measure_pins.py "$X/forge_r3_base.exe" "$O/final_base_pins.json" --depths 11,13
for e in o2 nozero speedstack; do
  nice -n 19 $PY -I -B $T/measure_pins.py "$X/forge_r3_$e.exe" "$O/final_${e}_pins.json" --depths 11,13
done
nice -n 19 $PY -I -B $T/measure_pins.py "$X/forge_r3_ttprefetch.exe" "$O/final_ttprefetch_pins.json" --depths 11,13 --set 'ON=TtChildPrefetch:true'
nice -n 19 $PY -I -B $T/measure_pins.py "$X/forge_r3_lazyacc.exe" "$O/final_lazyacc_pins.json" --depths 11,13 --set 'ON=NnueLazyAcc:true'
nice -n 19 $PY -I -B $T/measure_pins.py "$X/forge_r3_int16.exe" "$O/final_int16_pins.json" --depths 11,13 --set 'ON=NnueInt16:true'
( cd "$X" && sha256sum forge_r3_*.exe )
echo "spot check done $(date '+%F %T')"
