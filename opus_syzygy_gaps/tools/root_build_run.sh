#!/usr/bin/env bash
# root_build_run.sh <tag> <tables dir> <name> [Name=Value ...] - tb_root built from the candidate tree (a new tag per source
# state), run on the clock fixture, checked against python-chess. Output: out/exp/root/<tag>_<name>.*
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
tag=$1; tables=$2; name=$3
shift 3
DEFS=${ROOT_DEFS:-FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1}
FENS=${ROOT_FENS:-clock}
EXE=tb_root_$tag.exe
if [ ! -e "$J/out/exe/$EXE" ]; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/plain_build.ps1" -Src "$W\\out\\src\\${ROOT_SRC:-cand}" -Exe "$W\\out\\exe\\$EXE" \
    -Defines "$DEFS" -Units 'bitboard,board,book,eval,eval_params,nnue,search' \
    -MoreSources "$W\\repo\\opus_syzygy_gaps\\tools\\tb_root.cpp" 2>&1 | tail -1 | cut -c1-150
  grep -E 'error' "$J/out/exe/$EXE.build.log" | head -5 | cut -c1-200
fi
B="$J/out/exp/root/${tag}_$name"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$W\\out\\exe\\$EXE" \
  -ArgLine "$tables $W\\out\\exp\\root\\$FENS.fens 1 $*" \
  -OutFile "$W\\out\\exp\\root\\${tag}_$name.out" -ErrFile "$W\\out\\exp\\root\\${tag}_$name.err"
head -1 "$B.err" | cut -c1-100
python -I -B "$T/root_check.py" "$J/out/exp/root/$FENS.oracle.jsonl" "$B.out" --json "$B.check.json" --list "$B.bad.tsv"
awk -F'\t' '{print $1}' "$B.bad.tsv" | sort | uniq -c | tr '\n' ' '; echo
