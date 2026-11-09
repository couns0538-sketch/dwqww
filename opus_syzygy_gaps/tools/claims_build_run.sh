#!/usr/bin/env bash
# claims_build_run.sh <tag> [Name=Value ...] - instrumented copy of a tree (CLAIM_SRC, default cand), built with every candidate macro on (CLAIM_DEFS),
# run on the first CLAIM_FIRST lines of CLAIM_FENS at depth CLAIM_DEPTH, probes limited to CLAIM_CARD pieces, full set as truth. CLAIM_WARM=1: warm mode
# (lines fen TAB later clock). Reuses the build of the same tag (a new tag per source state). Results: out/exp/claims/<tag>_<options>_d<D>_n<N>[_<label>].out
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
tag=$1
shift
DEFS=${CLAIM_DEFS-FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1}
FIRST=${CLAIM_FIRST:-3000}
DEPTH=${CLAIM_DEPTH:-10}
CARD=${CLAIM_CARD:-4}
FENS=${CLAIM_FENS:-exp\\e1\\roots200k.fens}
LABEL=${CLAIM_LABEL:-}
EXE=tb_claims_$tag.exe
if [ ! -e "$J/out/exe/$EXE" ]; then
  python -I -B "$T/make_instr.py" "$J/out/src/${CLAIM_SRC:-cand}" "$J/out/src/instr_$tag" || exit 1
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/plain_build.ps1" -Src "$W\\out\\src\\instr_$tag" -Exe "$W\\out\\exe\\$EXE" \
    -Defines "$DEFS" -Units 'bitboard,board,book,eval,eval_params,nnue,search' \
    -MoreSources "$W\\repo\\opus_syzygy_gaps\\tools\\tb_claims.cpp" 2>&1 | tail -1 | cut -c1-150
  grep -E 'error' "$J/out/exe/$EXE.build.log" | head -5 | cut -c1-200
fi
name=$(echo "$tag $* d$DEPTH n$FIRST $LABEL" | tr ' =' '__')
if [ "${CLAIM_WARM:-0}" = 1 ]; then export TB_CLAIMS_WARM=1; fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$W\\out\\exe\\$EXE" \
  -ArgLine "D:\\syzygy345 $W\\out\\$FENS $CARD $DEPTH $FIRST 0 $*" \
  -OutFile "$W\\out\\exp\\claims\\$name.out" -ErrFile "$W\\out\\exp\\claims\\$name.err"
echo "== $name"
grep -vE 'events 0 wrong 0' "$J/out/exp/claims/$name.out" | cut -c1-110
