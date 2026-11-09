#!/usr/bin/env bash
# green_v8.sh <tag> - after a fix that must not change the rule-on full-table behaviour: the two RED tests of the bug check GREEN, and node identity with the earlier full suite (v6on).
#   1 UBSan and ASan root harness on boundary roots whose walk meets a missing table (gen_missing_child_fixture.py, `out/tb/nochild`): RED was a trap in `cap *= 4`.
#   2 rule off: SyzygyRule50=1 node-identical to SyzygyRule50=0 (RED: 651 of 6000 rows differed).
#   3 rule on, all switches on: root harness output byte-identical, engine rows identical on boundary, clock, 30000 roots above the tables.
# Output out/exp/hunt/green_<tag>.txt. Exits by itself.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
PY='C:\Python315\python.exe'
tag=$1
ON="SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3"
OA="--opt SyzygyTbBounds=7 --opt SyzygyRootExact=3 --opt SyzygyRule50=3"
DEFS='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
H=$J/out/exp/hunt; HW="$W\\out\\exp\\hunt"
O=$H/green_$tag.txt
Q=$J/out/qual/v6on
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
say() { echo "$*" | tee -a "$O" | cut -c1-240; }
[ -e "$J/out/exe/cand_${tag}_plain.exe" ] || ps "$T/plain_build.ps1" -Src "$W\\out\\src\\cand" -Exe "$W\\out\\exe\\cand_${tag}_plain.exe" -Defines "$DEFS" | tail -1 | cut -c1-110
[ -e "$J/out/exe/tb_root_$tag.exe" ] || ps "$T/plain_build.ps1" -Src "$W\\out\\src\\cand" -Exe "$W\\out\\exe\\tb_root_$tag.exe" -Defines "$DEFS" -Units 'bitboard,board,book,eval,eval_params,nnue,search' -MoreSources "$W\\repo\\opus_syzygy_gaps\\tools\\tb_root.cpp" | tail -1 | cut -c1-110
[ -e "$J/out/san/$tag" ] || ps "$T/sanitize_builds.ps1" -Src "$W\\out\\src\\cand" -Tag "$tag" -Defines "$DEFS" | tail -1 | cut -c1-100
say "head $(git -C "$J/out/src/cand" log -1 --format=%h) plain sha256 $(sha256sum "$J/out/exe/cand_${tag}_plain.exe" | cut -c1-64)"
for s in ubsan asan; do
  for d in nochild nodtz rejected wdl_only; do
    pin -Exe "$W\\out\\san\\$tag\\tb_root_$s.exe" -ArgLine "$W\\out\\tb\\$d $HW\\kqkr_b.fens 1 $ON" -OutFile "$HW\\kqkr_b_${s}_${tag}_$d.out" -ErrFile "$HW\\kqkr_b_${s}_${tag}_$d.err"
    say "missing child $s $d exit $? rows $(wc -l < "$H/kqkr_b_${s}_${tag}_$d.out") $(tail -1 "$H/kqkr_b_${s}_${tag}_$d.err" | cut -c1-90)"
  done
done
pin -Exe "$W\\out\\exe\\tb_root_$tag.exe" -ArgLine "$W\\out\\tb\\nochild $HW\\kqkr_b.fens 1 $ON" -OutFile "$HW\\kqkr_b_$tag.out" -ErrFile "$HW\\kqkr_b_$tag.err"
say "missing child plain: $(tail -1 "$H/kqkr_b_$tag.err" | cut -c1-120)"
say "  display column on nochild, top values: $(awk -F'\t' '{print $3}' "$H/kqkr_b_$tag.out" | sort | uniq -c | sort -rn | head -6 | tr -s ' ' | tr '\n' ';')"
for v in 0 1; do
  pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\cand_${tag}_plain.exe $HW\\r6k.fens $HW\\ruleoff_${tag}_$v.jsonl --tables $W\\out\\tb\\man34 --depth 10 --jobs 2 --opt Syzygy50MoveRule=false --opt SyzygyTbBounds=7 --opt SyzygyRule50=$v" -Log "$HW\\ruleoff_${tag}_$v.log"
done
say "rule off, SyzygyRule50 0 vs 1: $(python -I -B "$T/compare_runs.py" "$H/ruleoff_${tag}_0.jsonl" "$H/ruleoff_${tag}_1.jsonl" | cut -c1-150)"
pin -Exe "$W\\out\\exe\\tb_root_$tag.exe" -ArgLine "D:\\syzygy345 $W\\out\\exp\\exact\\b1.boundary.fens 1 $ON" -OutFile "$HW\\root_boundary_$tag.out" -ErrFile "$HW\\root_boundary_$tag.err"
say "root boundary against v6: $(cmp "$H/root_boundary_$tag.out" "$Q/root_boundary.out" && echo BYTE-IDENTICAL)"
pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\cand_${tag}_plain.exe $W\\out\\exp\\exact\\b1.boundary.fens $HW\\uci_boundary_$tag.jsonl --tables D:\\syzygy345 --depth 8 --jobs 3 $OA" -Log "$HW\\uci_boundary_$tag.log"
say "uci boundary against v6: $(python -I -B "$T/compare_runs.py" "$Q/uci_boundary.jsonl" "$H/uci_boundary_$tag.jsonl" | cut -c1-150)"
pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\cand_${tag}_plain.exe $W\\out\\exp\\root\\clock.fens $HW\\uci_clock_$tag.jsonl --tables D:\\syzygy345 --depth 6 --jobs 3 $OA" -Log "$HW\\uci_clock_$tag.log"
say "uci clock against v6: $(python -I -B "$T/compare_runs.py" "$Q/uci_clock.jsonl" "$H/uci_clock_$tag.jsonl" | cut -c1-150)"
pin -Exe "$PY" -ArgLine "-I -B $WT\\uci_tb.py $W\\out\\exe\\cand_${tag}_plain.exe $W\\out\\exp\\e1\\roots200k.fens $HW\\above30k_$tag.jsonl --tables $W\\out\\tb\\man34 --depth 10 --jobs 3 --first 30000 $OA" -Log "$HW\\above30k_$tag.log"
head -30000 "$Q/above_d10.jsonl" > "$H/above30k_v6.jsonl"
say "above tables, 30000 roots against v6: $(python -I -B "$T/compare_runs.py" "$H/above30k_v6.jsonl" "$H/above30k_$tag.jsonl" | cut -c1-150)"
say "end $(date)"
