#!/bin/bash
# Runtime options without recorded ON pins: bench nodes on the stack exe vs the option's own branch exe.
STACK=${1:-/f/opus_scratch/build/r3/m_s08.exe}
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
B=F:/opus_scratch/r3/tools/bench_opts.py
BUILD=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh
REF=/f/opus_scratch/build/r3/ref
mkdir -p $REF
build_ref() { # name worktree
  [ -f "$REF/$1.exe" ] || nice -n 19 bash $BUILD "$2" "$REF/$1.exe" > "$REF/$1.build.log" 2>&1
  echo "ref $1: $(git -C "$2" log --oneline -1 | cut -c1-60) sha256 $(sha256sum "$REF/$1.exe" | cut -c1-16)"
}
nodes() { nice -n 19 $PY -I -B $B "$@" 2>&1 | awk '/^bench/{printf "%s ", $4}'; }
cmp_opt() { # ref-name depths opts...
  local ref=$1 depths=$2; shift 2
  local a b
  a=$(nodes "$STACK" "$@" --depths "$depths"); b=$(nodes "$REF/$ref.exe" "$@" --depths "$depths")
  if [ "$a" = "$b" ]; then echo "MATCH    [$ref] $*: $a"; else echo "MISMATCH [$ref] $*: stack [$a] branch [$b]"; fi
}
build_ref c2 /d/grok-pc-data/dwqww/.claude/worktrees/opus_c2
build_ref s41 /f/opus_scratch/worktrees/opus_sol_s41
build_ref c1 /d/grok-pc-data/dwqww/.claude/worktrees/opus_c1
build_ref a1 /f/opus_scratch/worktrees/opus_sol_a1
build_ref ltt /d/grok-pc-data/dwqww/.claude/worktrees/opus_ltt
for v in 1 2 4 7; do cmp_opt c2 11,13,16 --opt CorrHistPlus=$v; done
for v in 90 110; do cmp_opt s41 11,13,16 --opt NetScale=$v; done
cmp_opt a1 11,13,16 --opt HistRework=3
cmp_opt c1 11,13,16 --opt SyzygyPath=D:/grok-pc-data/dwqww/.claude/worktrees/syzygy345
cmp_opt ltt 11,13,16 --opt LocklessTT=true
