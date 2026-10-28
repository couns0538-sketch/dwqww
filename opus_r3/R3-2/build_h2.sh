#!/usr/bin/env bash
# R3-2, stack head 2047348a (merged into opus-r3-matrix): rebuild the switch set of build_all.sh from the merged source
# (*_h2.exe) and compare each with the exe of the first pass (only the PE timestamp/checksum may differ), then build the
# new exes: lazy (FORGE_NNUE_LAZY_ACC), o2_lazy (+ FORGE_NNUE_O2), prof (FORGE_PROF, src/profile.cpp added).
# usage: nice -n 19 bash opus_r3/R3-2/build_h2.sh <worktree> <build_dir>
set -uo pipefail
SRC=$1; OUT=$2
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LA=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
build() {   # build <name> [flags...]
  local name=$1; shift
  echo "=== build $name flags: $* extra srcs: ${FORGE_EXTRA_SRCS:-none} (free RAM $(free_gb) GB) $(date '+%F %T')"
  nice -n 19 bash "$T/build_pc.sh" "$SRC" "$OUT/$name.exe" "$@" 2>&1
}
cd "$SRC" && echo "source $(git rev-parse HEAD) (merge of opus-r3-stack 2047348a); $(git status --short | wc -l) dirty paths"
build base_h2
build o2_h2 -DFORGE_NNUE_O2=1
build nozero_h2 -DFORGE_NOZERO_MOVE_BUFFERS=1
build s13_h2 -DFORGE_S13_TT_CHILD_PREFETCH=1
build speedstack_h2 -DFORGE_SPEEDSTACK=1
build ss_s13_h2 -DFORGE_SPEEDSTACK=1 -DFORGE_S13_TT_CHILD_PREFETCH=1
build lazy -DFORGE_NNUE_LAZY_ACC=1
build o2_lazy -DFORGE_NNUE_O2=1 -DFORGE_NNUE_LAZY_ACC=1
FORGE_EXTRA_SRCS=src/profile.cpp build prof -DFORGE_PROF=1
echo "=== first-pass exe vs the same switches built from the merged head (cmp -l: differing bytes; PE timestamp/checksum = about 5-6)"
for e in base o2 nozero s13 speedstack ss_s13; do
  n=$(cmp -l "$OUT/$e.exe" "$OUT/${e}_h2.exe" | wc -l)
  echo "$e.exe vs ${e}_h2.exe: $n differing bytes; offsets: $(cmp -l "$OUT/$e.exe" "$OUT/${e}_h2.exe" | awk '{print $1}' | tr '\n' ' ' | cut -c1-80)"
done
echo "=== sha256"
(cd "$OUT" && sha256sum base_h2.exe lazy.exe o2_lazy.exe prof.exe)
echo "=== identity of the new exes (options off = lock pins)"
for e in base_h2 lazy o2_lazy prof; do
  echo "--- $e"
  nice -n 19 "$PY" -I -B "$LA/2_build/uci_check.py" "$OUT/$e.exe" 2>&1
done
echo "=== done $(date '+%F %T')"
