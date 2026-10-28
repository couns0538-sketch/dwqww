#!/usr/bin/env bash
# R3-2, final R3-1 stack head 330237f3 (merged into opus-r3-matrix): the exes of the head-3 configurations, one g++
# at a time (PC lock recipe), then a byte compare of the two OFF exes and the lock-pin identity of every new exe with
# its options off. The default build of this head contains the HardDeadline output fix, so it is not expected to be
# byte-identical to the first-pass base.exe (467a59b3); H3DRIFT in r3_matrix.py times the two.
# usage: nice -n 19 bash opus_r3/R3-2/build_final_head.sh <worktree> <build_dir>
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
cd "$SRC" && echo "source $(git rev-parse HEAD) (opus-r3-matrix with opus-r3-stack 330237f3 merged); $(git status --short -- src include | wc -l) dirty engine paths"
build base_h3
build o2_h3 -DFORGE_NNUE_O2=1
build lazy -DFORGE_NNUE_LAZY_ACC=1
build o2_lazy -DFORGE_NNUE_O2=1 -DFORGE_NNUE_LAZY_ACC=1
build int16 -DFORGE_NNUE_INT16=1
build o2_int16 -DFORGE_NNUE_O2=1 -DFORGE_NNUE_INT16=1
build int16_lazy -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_LAZY_ACC=1
FORGE_EXTRA_SRCS=src/profile.cpp build prof -DFORGE_PROF=1
echo "=== first-pass OFF exe vs final-head OFF exe (cmp -l differing bytes; the PE timestamp/checksum alone is 5-6)"
for p in "base base_h3" "o2 o2_h3"; do
  set -- $p
  echo "$1.exe vs $2.exe: $(cmp -l "$OUT/$1.exe" "$OUT/$2.exe" 2>/dev/null | wc -l) differing bytes; sizes $(stat -c %s "$OUT/$1.exe") / $(stat -c %s "$OUT/$2.exe")"
done
echo "=== sha256"
(cd "$OUT" && sha256sum base_h3.exe o2_h3.exe lazy.exe o2_lazy.exe int16.exe o2_int16.exe int16_lazy.exe prof.exe)
echo "=== identity of the final-head exes, options off (= lock pins)"
for e in base_h3 o2_h3 lazy o2_lazy int16 o2_int16 int16_lazy prof; do
  full=""; [ "$e" = base_h3 ] && full="--full"
  echo "--- $e $full"
  nice -n 19 "$PY" -I -B "$LA/2_build/uci_check.py" "$OUT/$e.exe" $full 2>&1
done
echo "=== done $(date '+%F %T')"
