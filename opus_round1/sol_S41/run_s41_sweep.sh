#!/usr/bin/env bash
# S41 tree-size evidence (nice 19, sequential): (1) 100 fixed self-play positions (set lines 301-400) at depth 12,
# OFF then ON in one process, for AL1 @ NetScale 99 and 90 and e48f006 @ 99; (2) a NetScale sweep of the 5-depth
# bench on the AL1 exe (95 97 98 101 103 105) and the e48f006 exe (98 101), to show how much single-position bench
# node counts move for a 1-5% evaluation rescale.
# usage: run_s41_sweep.sh <worktree> <build_dir> <out_dir> <positions.txt>
set -uo pipefail
W=$1; B=$2; OUT=$3; POS=$4
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=$W/opus_round1/sol_S41/tools
AL1_REF=312866,862329,3024920,12389307,34048354
F006_REF=328459,945640,3024381,9162399,20421972
mkdir -p "$OUT"
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
need_ram() { local f; f=$(free_gb); echo "free RAM ${f} GB before: $1"; awk -v f="$f" 'BEGIN{exit !(f>=6.0)}' || { echo "free RAM below 6 GB, stop"; exit 3; }; }
echo "# S41 sweep $(date); machine exclusive: no; nice 19"
for spec in "forge_s41_al1.exe 99" "forge_s41_al1.exe 90" "forge_s41_e48f006.exe 99"; do
  set -- $spec
  need_ram "node_ratio $1 NetScale=$2"
  nice -n 19 $PY -I -B $T/node_ratio.py "$B/$1" --fens "$POS" --first 300 --count 100 --depth 12 --on NetScale=$2 --json "$OUT/node_ratio_${1%.exe}_$2.json"
done
for pct in 95 97 98 101 103 105; do
  need_ram "AL1 bench NetScale=$pct"
  nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_s41_al1.exe" --ref $AL1_REF --opt NetScale=$pct --label "AL1 NetScale=$pct" --json "$OUT/al1_on_$pct.json" | grep -v "^ALL\|^MISMATCH"
done
for pct in 98 101; do
  need_ram "e48f006 bench NetScale=$pct"
  nice -n 19 $PY -I -B $T/bench_ref.py "$B/forge_s41_e48f006.exe" --ref $F006_REF --opt NetScale=$pct --label "e48f006 NetScale=$pct" --json "$OUT/e48f006_on_$pct.json" | grep -v "^ALL\|^MISMATCH"
done
echo "# done $(date)"
