#!/usr/bin/env bash
# budget_scan.sh - time and resolution of the boundary walk at several budgets, boundary fixture, tb_root builds with -DFORGE_SYZYGY_BOUNDARY_BUDGET.
set -u
J=/d/forge_jobs_20261107/opus1
W='D:\forge_jobs_20261107\opus1'
T=$J/repo/opus_syzygy_gaps/tools
DEFS='FORGE_SYZYGY_TB_BOUNDS=1,FORGE_SYZYGY_ROOT_EXACT=1,FORGE_SYZYGY_RULE50=1'
for b in "$@"; do
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/plain_build.ps1" -Src "$W\out\src\cand" -Exe "$W\out\exe\tb_root_w$b.exe" -Defines "$DEFS,FORGE_SYZYGY_BOUNDARY_BUDGET=$b" -Units 'bitboard,board,book,eval,eval_params,nnue,search' -MoreSources "$W\repo\opus_syzygy_gaps\tools\tb_root.cpp" 2>&1 | tail -1 | cut -c1-60
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/pinned.ps1" -Exe "$W\out\exe\tb_root_w$b.exe" -ArgLine "D:\syzygy345 $W\out\exp\exact\b1.boundary.fens 1 SyzygyRootExact=3" -OutFile "$W\out\exp\exact\b$b.out" -ErrFile "$W\out\exp\exact\b$b.err"
  echo "budget $b: $(tail -1 "$J/out/exp/exact/b$b.err" | cut -c1-110)"
  python -I -B - "$J/out/exp/exact/b$b.out" <<'PY'
import sys
n=und=0
for l in open(sys.argv[1]):
    p=l.rstrip('\n').split('\t')
    if len(p)<7: continue
    n+=1
    if any(x.split(':')[-3] in ('900','-900') for x in p[6].split()): und+=1
print('  roots',n,'with an undecided boundary move',und)
PY
done
