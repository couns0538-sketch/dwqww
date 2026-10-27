#!/usr/bin/env bash
# S25fix on Linux (GitHub runner): the v2 output-contract checker against a Linux build of this tree (the AL1 lock
# engine), its 17 tests, and the v3 CMake registration (ctest target) on a patched copy. Closes the REPORT's
# "Linux run of the v2 checker: UNVERIFIED". Read-only on the repo; writes only under <out_dir>.
# usage: opus_round1/sol_S25fix/ci_s25fix_linux.sh <out_dir>
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
J="$ROOT/opus_round1/sol_S25fix"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
status=0
cmake -S "$ROOT" -B "$OUT/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$FLAGS" \
  > "$OUT/configure.log" 2>&1 || { tail -30 "$OUT/configure.log"; exit 1; }
cmake --build "$OUT/build" --target forge -j"$(nproc)" > "$OUT/build.log" 2>&1 || { tail -40 "$OUT/build.log"; exit 1; }
CHK="$J/forge_sol_S25_outcontract_v2_20261027.py"
python3 -I -B "$CHK" "$OUT/build/forge" --depths all --out "$OUT/run_al1_all" > "$OUT/run_al1_all.log" 2>&1
rc=$?; echo "AL1 pins, all depths: exit $rc :: $(grep OUTPUT_CONTRACT "$OUT/run_al1_all.log" | tail -1)"; [ $rc -eq 0 ] || status=1
python3 -I -B "$CHK" "$OUT/build/forge" --ref Lprime --out "$OUT/run_lprime" > "$OUT/run_lprime.log" 2>&1
rc=$?; line=$(grep OUTPUT_CONTRACT "$OUT/run_lprime.log" | tail -1)
echo "Lprime pins (expect exit 1, bench=PIN_MISMATCH, uci=PASS): exit $rc :: $line"
{ [ $rc -eq 1 ] && echo "$line" | grep -q 'bench=PIN_MISMATCH' && echo "$line" | grep -q 'uci=PASS'; } || status=1
mkdir -p "$OUT/scratch"
S25_SCRATCH="$OUT/scratch" python3 -I -B "$J/test_forge_sol_S25_outcontract_v2_20261027.py" -v > "$OUT/tests_linux.log" 2>&1 || status=1
tail -4 "$OUT/tests_linux.log"
# v3 registration patch: apply to a clean copy of this tree, configure ON, run the ctest target
mkdir -p "$OUT/src_v3" && git -C "$ROOT" archive HEAD CMakeLists.txt bench include src tests tools opus_round1/sol_S25fix | tar -x -m -C "$OUT/src_v3"
# GNU patch, not git apply: ci_out/ lies inside the checkout, and git apply run from a subdirectory of a work tree
# treats "diff --git" paths as repo-root relative and silently skips them (exit 0, nothing applied; seen in run 40521419392).
(cd "$OUT/src_v3" && patch -p1 -F0 --no-backup-if-mismatch --dry-run < "$J/forge_sol_S25_outcontract_v3_20261027.patch" \
  && patch -p1 -F0 --no-backup-if-mismatch < "$J/forge_sol_S25_outcontract_v3_20261027.patch") > "$OUT/v3_apply.log" 2>&1 || { cat "$OUT/v3_apply.log"; status=1; }
grep -q 'FORGE_OUTPUT_CONTRACT' "$OUT/src_v3/CMakeLists.txt" || { echo "v3 patch not applied"; status=1; }
cmake -S "$OUT/src_v3" -B "$OUT/build_v3" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$FLAGS" \
  -DFORGE_OUTPUT_CONTRACT=ON > "$OUT/configure_v3.log" 2>&1 || { tail -30 "$OUT/configure_v3.log"; status=1; }
cmake --build "$OUT/build_v3" --target forge -j"$(nproc)" > "$OUT/build_v3.log" 2>&1 || { tail -30 "$OUT/build_v3.log"; status=1; }
(cd "$OUT/build_v3" && ctest -R forge_sol_S25 --output-on-failure) > "$OUT/ctest_v3_on.log" 2>&1 || status=1
grep -q 'No tests were found' "$OUT/ctest_v3_on.log" && { echo "ctest found no S25 test (registration missing)"; status=1; }
grep -E 'tests passed|Passed|Failed|No tests' "$OUT/ctest_v3_on.log" | tail -3
echo "ci_s25fix_linux status=$status"
exit $status
