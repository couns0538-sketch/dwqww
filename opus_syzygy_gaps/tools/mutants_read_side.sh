#!/usr/bin/env bash
# mutants_read_side.sh <tag> - fixture for the two read-side rules of SyzygyRule50 bit 1 that had no test that could fail (review/H1.md, finding 1), with the mutants that must fail it. Test first: the mutants are RED, the frozen head GREEN.
#   rows: gen_warm_read_fixture.py, kinds k0 and mate, out/exp/read/rows_<kind>.tsv. Exes: claim harness of the head, of m7 (mate + clock <= 101), of m8 (distance 0 usable at any clock), of m1 (TB distance + clock <= 101, an older mutant, as a control of the rows).
#   runs: head all on; head without bit 1 (SyzygyRule50=2); each mutant all on. Summary: out/exp/read/SUMMARY_<tag>.txt: wrong counts per site, a line per run. Exit 1 if the head has a wrong returned claim or a mutant survives its row kind.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
WT="$W\\repo\\opus_syzygy_gaps\\tools"
VPY='C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
DEFS='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
ON='SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3'
CTL='SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=2'
tag=$1
R=$J/out/exp/read; RW="$W\\out\\exp\\read"
S=$R/SUMMARY_$tag.txt
mkdir -p "$R"
pin() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" "$@"; }
say() { echo "$*" | tee -a "$S" | cut -c1-170; }
say "start $(date) head $(git -C "$J/out/src/cand" log -1 --format=%h)"
for k in k0 mate; do
  [ -e "$R/rows_$k.tsv" ] || pin -Exe "$VPY" -ArgLine "-I -B $WT\\gen_warm_read_fixture.py D:\\syzygy345 $RW\\rows_$k.tsv --kind $k --rows ${ROWS:-1500}" -Log "$RW\\rows_$k.log"
  say "rows $k: $(wc -l < "$R/rows_$k.tsv") $(tail -1 "$R/rows_$k.log" | cut -c1-80)"
done
build() { # build <name> [<old> <new>]
  local n=$1 tree=$J/out/src/mut_${tag}_$1 instr=$J/out/src/instrr_${tag}_$1
  mkdir -p "$tree"
  git -C "$J/out/src/cand" -c core.autocrlf=false archive HEAD | tar -x -C "$tree"
  if [ $# -gt 1 ]; then python -I -B "$T/mutate_one.py" "$tree/src/search.cpp" "$2" "$3" || exit 1; fi
  python -I -B "$T/make_instr.py" "$tree" "$instr" || exit 1
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/plain_build.ps1" -Src "$W\\out\\src\\instrr_${tag}_$n" -Exe "$W\\out\\exe\\tbr_${tag}_$n.exe" -Defines "$DEFS" -Units 'bitboard,board,book,eval,eval_params,nnue,search' -MoreSources "$WT\\tb_claims.cpp" 2>&1 | tail -1 | cut -c1-120
  [ -e "$J/out/exe/tbr_${tag}_$n.exe" ] || { say "FAIL build $n"; exit 1; }
}
build head
build m7 'return MateValue - magnitude + clock <= 100;' 'return MateValue - magnitude + clock <= 101;'
build m8 'return k == 0 ? clock == 0 : k + clock <= 100;' 'return k == 0 ? true : k + clock <= 100;'
build m1 'return k == 0 ? clock == 0 : k + clock <= 100;' 'return k == 0 ? clock == 0 : k + clock <= 101;'
export TB_CLAIMS_WARM=2
wrongs() { grep -E '^site ' "$1" | grep -v 'site null_raw' | awk '{w += $6; e += $4} END {print "events", e, "wrong", w}'; }
run() { # run <exe name> <rows kind> <depth> <label> <options>
  local o=$R/run_${tag}_$1_$2_$4
  pin -Exe "$W\\out\\exe\\tbr_${tag}_$1.exe" -ArgLine "D:\\syzygy345 $RW\\rows_$2.tsv 4 $3 0 0 $5" -OutFile "$RW\\run_${tag}_$1_$2_$4.out" -ErrFile "$RW\\run_${tag}_$1_$2_$4.err"
  say "$1 $2 $4 depth $3 exit $?: $(wrongs "$o.out") | $(grep -E '^site ' "$o.out" | grep -vE 'wrong 0 ' | awk '{printf "%s %s/%s; ", $2, $6, $4}')"
}
fails=0
expect_zero() { w=$(wrongs "$R/run_${tag}_$1_$2_$3.out" | awk '{print $4}'); if [ "$w" != 0 ]; then say "FAILED: $1 $2 $3 has $w wrong"; fails=$((fails + 1)); fi; }
expect_red() { w=$(wrongs "$R/run_${tag}_$1_$2_$3.out" | awk '{print $4}'); if [ "$w" = 0 ]; then say "FAILED: mutant $1 survives rows $2"; fails=$((fails + 1)); fi; }
D_K0=${DEPTH_K0:-12}
D_MATE=${DEPTH_MATE:-14}
run head k0 $D_K0 on "$ON"; run head mate $D_MATE on "$ON"
run head k0 $D_K0 ctl "$CTL"; run head mate $D_MATE ctl "$CTL"
run m8 k0 $D_K0 on "$ON"; run m7 mate $D_MATE on "$ON"
run m1 k0 $D_K0 on "$ON"; run m8 mate $D_MATE on "$ON"; run m7 k0 $D_K0 on "$ON"
expect_zero head k0 on; expect_zero head mate on
expect_red m8 k0 on; expect_red m7 mate on
say "end $(date) failed checks $fails"
[ "$fails" -eq 0 ] && say "VERDICT read-side rows: head clean, mutants caught" || say "VERDICT read-side rows: $fails CHECKS FAILED"
[ "$fails" -eq 0 ]
