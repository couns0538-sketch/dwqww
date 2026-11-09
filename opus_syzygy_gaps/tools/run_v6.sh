#!/usr/bin/env bash
# run_v6.sh <tag> - the whole suite on a candidate tree state: plain engine, root harness, sanitizers, then fixtures, partial tables, sanitizer runs, per-bit quality runs.
# All pinned. A new tag per source state. Results: out/qual/<tag>/, out/exp/partial/<tag>/, out/san/<tag>/. Exits by itself.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
tag=$1
DEFS='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
ON="SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3"
export QUAL_JOBS=${QUAL_JOBS:-3}
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
[ -e "$J/out/exe/cand_${tag}_plain.exe" ] || ps "$T/plain_build.ps1" -Src "$W\\out\\src\\cand" -Exe "$W\\out\\exe\\cand_${tag}_plain.exe" -Defines "$DEFS" | tail -1 | cut -c1-110
[ -e "$J/out/exe/tb_root_$tag.exe" ] || ps "$T/plain_build.ps1" -Src "$W\\out\\src\\cand" -Exe "$W\\out\\exe\\tb_root_$tag.exe" -Defines "$DEFS" -Units 'bitboard,board,book,eval,eval_params,nnue,search' -MoreSources "$W\\repo\\opus_syzygy_gaps\\tools\\tb_root.cpp" | tail -1 | cut -c1-110
[ -e "$J/out/san/$tag" ] || ps "$T/sanitize_builds.ps1" -Src "$W\\out\\src\\cand" -Tag "$tag" -Defines "$DEFS" | tail -1 | cut -c1-100
QUAL_STEPS='root uci toggle warm playout misc quality' bash "$T/qual_all.sh" "${tag}on" "cand_${tag}_plain" "$tag" "h${tag}" $ON
bash "$T/special2.sh" "${tag}on" "cand_${tag}_plain" "$tag" $ON
QUAL_STEPS='claims' bash "$T/qual_all.sh" "${tag}on" "cand_${tag}_plain" "$tag" "h${tag}" $ON
bash "$T/run_partial.sh" "${tag}on" "$tag" "cand_${tag}_plain" $ON
ps "$T/run_san.ps1" -Tag "$tag" -Jobs 2
ps "$T/run_flip_asan.ps1" -Tag "$tag"
echo "done $tag"
