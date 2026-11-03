#!/usr/bin/env bash
# hash_sweep_r14b.sh OUT_FILE - Opus R14-B: every hash the R14-B documents cite (the three opus_r14b trees, the skills
# forge-relabel-job / forge-npt-fast-loader / forge-opus-tools, the memory note) must match a real file, a commit of
# the repository or a reasoned allow-list entry (tools/hash_sweep_allow.txt). Runs hash_sweep.py pinned to CPUs 2-3 at
# BelowNormal. The other skills R14-B touched (forge-pc-rules, forge-ltopgo-pgo, forge-nnue-data) also cite older jobs'
# artifacts that are not R14-B claims, so they are not part of this sweep. Exit 0 = nothing unmatched.
set -u
out=${1:?out file}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
W=/d/grok-pc-data/dwqww/.claude/worktrees
T=$W/o14b-status/opus_r14b/tools
docs=$(find "$W/o14b-status/opus_r14b" "$W/o14b-l1/opus_r14b" "$W/o14b-r2/opus_r14b" -name "*.md" -not -path "*/logs/*")
docs="$docs /d/grok-pc-data/dwqww/.claude/skills/forge-relabel-job/SKILL.md"
docs="$docs /d/grok-pc-data/dwqww/.claude/skills/forge-npt-fast-loader/SKILL.md"
docs="$docs /d/grok-pc-data/dwqww/.claude/skills/forge-opus-tools/SKILL.md"
docs="$docs /c/Users/Administrator/.claude/projects/D--grok-pc-data-dwqww/memory/opus-r14b-status.md"
files="$W/o14b-status/opus_r14b $W/o14b-l1/opus_r14b $W/o14b-r2/opus_r14b $W/o14b-r2/opus_r13/p5/forge_data_probe.cpp"
files="$files /d/o14b/fl/b5_install /d/o14b/ref /c/o13/p5/forge_data_probe.exe /c/o14b/pgo2 /f/opus_scratch/rescore_d8/bin"
files="$files /d/o14b/r2/proof/jobA/final /d/o14b/r2/proof/jobB/final /d/o14b/r2/proof/jobA/rows.tsv /c/o14b/r2/pgo_full/final"
files="$files /d/o14b/npt/config.py /d/o14b/npt/train.py /d/o14b/npt/opus_tools/guard_exec.py"
for f in $files; do [ -e "$f" ] || { echo "missing input $f" >&2; exit 2; }; done
args="-I -B $(cygpath -w "$T/hash_sweep.py") --docs"
for d in $docs; do args="$args $(cygpath -w "$d")"; done
args="$args --files"
for f in $files; do args="$args $(cygpath -w "$f")"; done
args="$args --repo $(cygpath -w /d/grok-pc-data/dwqww) --allow $(cygpath -w "$T/hash_sweep_allow.txt")"
powershell -NoProfile -File "$(cygpath -w "$T/lowrun.ps1")" -Mask 0xC -Priority BelowNormal \
  -Exe "$(cygpath -w /c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe)" -ArgLine "$args" \
  -Out "$(cygpath -w "$out")" -Err "$(cygpath -w "$out").err"
rc=$?
cat "$out"
exit $rc
