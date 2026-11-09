#!/usr/bin/env bash
# run_partial.sh <tag> <tb_root exe tag> <engine exe name> [Name=Value ...] - partial and damaged table folders. Output out/exp/partial/<tag>/. Results in SUMMARY.txt
# tb_root: load line, exit code, no crash. Engine at depth 5: legal moves over the same rows, TB-band claims counted per folder (none may rest on a missing table).
# The damaged folders run under ASan with tools/run_flip_asan.ps1.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
tag=$1; root=$2; exe=$3
shift 3
OPTS=("$@")
OPTARGS=""; for o in "${OPTS[@]}"; do OPTARGS="$OPTARGS --opt $o"; done
O=$J/out/exp/partial/$tag; OW="$W\\out\\exp\\partial\\$tag"
mkdir -p "$O"
S=$O/SUMMARY.txt
F="$W\\out\\exp\\partial\\mix.fens"
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
for d in nodtz nochild dtzonly rejected; do
  pin -Exe "$W\\out\\exe\\tb_root_$root.exe" -ArgLine "$W\\out\\tb\\$d $F 1 ${OPTS[*]-}" -OutFile "$OW\\$d.out" -ErrFile "$OW\\$d.err"
  rc=$?
  echo "$d tb_root exit $rc: $(head -1 "$O/$d.err" | cut -c1-80) | ranked $(awk -F'\t' '$6!="-"' "$O/$d.out" | wc -l) of $(wc -l < "$O/$d.out"), shown $(awk -F'\t' '$3!="-"' "$O/$d.out" | wc -l)" >> "$S"
  if [ ! -e "$O/$d.jsonl" ]; then pin -Exe 'C:\Python315\python.exe' -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\$exe.exe $F $OW\\$d.jsonl --tables $W\\out\\tb\\$d --depth 5 --jobs 2 $OPTARGS" -Log "$OW\\$d.log"; fi
  echo "$d engine: $(head -1 "$O/$d.log" | cut -c1-90)" >> "$S"
  python -I -B - "$O/$d.jsonl" "$J/out/exp/partial/mix.oracle.jsonl" >> "$S" <<'PY'
import json,sys
oracle={}
for l in open(sys.argv[2]):
    r=json.loads(l); oracle[r['fen']]=r
claims=false_claims=illegal=0
for l in open(sys.argv[1]):
    r=json.loads(l); o=oracle[r['fen']]
    if o['moves'] and r['bestmove'] not in {m['uci'] for m in o['moves']}: illegal+=1
    s=r.get('score') or 0
    if r.get('score_type')=='cp' and abs(s)>=31743:
        claims+=1
        d=o['dtz']
        if d is None or (s>0)!=(d>0) or abs(d)+o['clock']>100: false_claims+=1
print('  engine: TB-band root scores',claims,'against the full-set oracle wrong',false_claims,'illegal moves',illegal)
PY
done
