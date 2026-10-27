#!/usr/bin/env bash
# A2 microbench: apply checks, OFF = no code, lock identity, ON counters. Everything under nice 19, 1 thread.
# usage: bash a2_verify.sh <scratch_dir> <log_dir>
#   <scratch_dir> must not exist yet (fresh copies and exes go there); logs go to <log_dir>.
# Inputs (read only): the lock source LA/1_source/forge_AL1_s198_src, the PC lock exe, the box build script.
set -euo pipefail
S=$1; L=$2
HERE=$(cd "$(dirname "$0")" && pwd)
PATCH=$HERE/forge_astra_A2_kbstats_microbench_20261027.patch
LA=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LOCK_EXE=/d/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_h256_s198.exe
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
OBJDUMP=/c/msys64/ucrt64/bin/objdump.exe
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
[ -e "$S" ] && { echo "scratch dir $S exists; give a new one"; exit 2; }
mkdir -p "$S/tmp" "$L"
export TMP=$S/tmp TEMP=$S/tmp

{
echo "== patch"
sha256sum "$PATCH"
echo "== git apply --check / patch -p1 -F0 on fresh copies of LA/1_source/forge_AL1_s198_src"
cp -r "$LA/1_source/forge_AL1_s198_src" "$S/check_git"
cp -r "$LA/1_source/forge_AL1_s198_src" "$S/check_patch"
(cd "$S/check_git" && git apply --check -v "$PATCH") && echo "git apply --check: OK"
(cd "$S/check_patch" && patch -p1 -F0 --dry-run < "$PATCH") && echo "patch -p1 -F0 --dry-run: OK"
echo "== patched tree (patch -p1 -F0) and pristine tree"
cp -r "$LA/1_source/forge_AL1_s198_src" "$S/patched"
(cd "$S/patched" && patch -p1 -F0 < "$PATCH")
cp -r "$LA/1_source/forge_AL1_s198_src" "$S/pristine"
} 2>&1 | tee "$L/apply_check.log"

{
echo "== builds (box recipe $T/build_pc.sh: g++ 15.2 ucrt64 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=znver5 -static, FMA off)"
nice -n 19 bash "$T/build_pc.sh" "$S/pristine" "$S/forge_lock_ref.exe"
nice -n 19 bash "$T/build_pc.sh" "$S/patched" "$S/forge_a2_off.exe"
nice -n 19 bash "$T/build_pc.sh" "$S/patched" "$S/forge_a2_on.exe" -DFORGE_A2_KBSTATS
echo "== OFF = no code"
echo "cmp -l forge_a2_off.exe forge_lock_ref.exe (pristine lock source, same recipe): $(cmp -l "$S/forge_a2_off.exe" "$S/forge_lock_ref.exe" | wc -l) differing bytes"
cmp -l "$S/forge_a2_off.exe" "$S/forge_lock_ref.exe" || true
cp "$LOCK_EXE" "$S/forge_h256_s198_lock.exe"
echo "PC lock exe sha256 $(sha256sum "$S/forge_h256_s198_lock.exe" | cut -d' ' -f1)"
echo "cmp -l forge_a2_off.exe forge_h256_s198_lock.exe (the PC lock exe): $(cmp -l "$S/forge_a2_off.exe" "$S/forge_h256_s198_lock.exe" | wc -l) differing bytes"
cmp -l "$S/forge_a2_off.exe" "$S/forge_h256_s198_lock.exe" || true
export PATH=/c/msys64/ucrt64/bin:$PATH
for f in src/search.cpp src/uci.cpp src/eval.cpp src/nnue.cpp; do
  for t in patched pristine; do
    (cd "$S/$t" && nice -n 19 g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math \
       -march=znver5 -Iinclude -E -P "$f" -o "$S/pp_${t}_$(basename "$f").i")
  done
  if cmp -s "$S/pp_patched_$(basename "$f").i" "$S/pp_pristine_$(basename "$f").i"; then r=IDENTICAL; else r=DIFFERENT; fi
  echo "g++ -E -P (OFF flags) $f patched vs pristine: $r sha256 $(sha256sum "$S/pp_patched_$(basename "$f").i" | cut -c1-16)"
done
} 2>&1 | tee "$L/build_and_off_identity.log"

{
echo "\$ nice -n 19 python -I -B LA/2_build/uci_check.py forge_a2_off.exe --full   (exe sha256 $(sha256sum "$S/forge_a2_off.exe" | cut -d' ' -f1))"
nice -n 19 "$PY" -I -B "$LA/2_build/uci_check.py" "$S/forge_a2_off.exe" --full
echo "FMA count (objdump -d | grep -cE 'vfn?m(add|sub)'): $("$OBJDUMP" -d "$S/forge_a2_off.exe" | grep -cE 'vfn?m(add|sub)' || true)"
} 2>&1 | tee "$L/identity_off.log"

{
echo "\$ nice -n 19 python -I -B LA/2_build/uci_check.py forge_a2_on.exe --full   (exe sha256 $(sha256sum "$S/forge_a2_on.exe" | cut -d' ' -f1); -DFORGE_A2_KBSTATS)"
nice -n 19 "$PY" -I -B "$LA/2_build/uci_check.py" "$S/forge_a2_on.exe" --full
echo "FMA count (objdump -d | grep -cE 'vfn?m(add|sub)'): $("$OBJDUMP" -d "$S/forge_a2_on.exe" | grep -cE 'vfn?m(add|sub)' || true)"
} 2>&1 | tee "$L/identity_on.log"

{
echo "\$ nice -n 19 python -I -B a2_kbstats_run.py forge_a2_on.exe kbstats_raw.log 16 20 22"
nice -n 19 "$PY" -I -B "$HERE/a2_kbstats_run.py" "$S/forge_a2_on.exe" "$L/kbstats_raw.log" 16 20 22
} 2>&1 | tee "$L/kbstats_run.log"
echo "a2_verify done"
