#!/usr/bin/env bash
# R3-2: build the six PC-recipe exes of the interaction matrix, one g++ at a time, then copy base.exe to
# base_copy.exe (A/A control). Every exe is checked for the lock pins (uci_check.py, d11/13/16; base --full).
# usage: nice -n 19 bash opus_r3/R3-2/build_all.sh <worktree> <build_dir>     (Git Bash; pass absolute paths)
set -uo pipefail
SRC=$1; OUT=$2
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LA=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
mkdir -p "$OUT"
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }
build() {   # build <name> [flags...]
  local name=$1; shift
  echo "=== build $name flags: $* (free RAM $(free_gb) GB) $(date '+%F %T')"
  nice -n 19 bash "$T/build_pc.sh" "$SRC" "$OUT/$name.exe" "$@" 2>&1
}
cd "$SRC" && echo "source $(git rev-parse HEAD) $(git status --short | wc -l) dirty paths"
build base
build o2 -DFORGE_NNUE_O2=1
build nozero -DFORGE_NOZERO_MOVE_BUFFERS=1
build s13 -DFORGE_S13_TT_CHILD_PREFETCH=1
build speedstack -DFORGE_SPEEDSTACK=1
build ss_s13 -DFORGE_SPEEDSTACK=1 -DFORGE_S13_TT_CHILD_PREFETCH=1
cp "$OUT/base.exe" "$OUT/base_copy.exe"
echo "=== sha256"
(cd "$OUT" && sha256sum base.exe base_copy.exe o2.exe nozero.exe s13.exe speedstack.exe ss_s13.exe)
echo "=== identity (option OFF = lock pins)"
for e in base o2 nozero s13 speedstack ss_s13; do
  full=""; [ "$e" = base ] && full="--full"
  echo "--- $e $full"
  nice -n 19 "$PY" -I -B "$LA/2_build/uci_check.py" "$OUT/$e.exe" $full 2>&1
done
echo "=== done $(date '+%F %T')"
