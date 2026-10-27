#!/usr/bin/env bash
# S05fix Linux evidence for the v4 FMA checker on real ELF binaries (used by .github/workflows/opus-sol-s05fix-ci.yml).
# Box flags, g++-14, CMake Release. Engine sources are not changed by this branch.
#   1. default build (= lock 294dbed source): v4 must PASS with computed counts 0 (whole .text and whole binary);
#      Sol's v3 is run on the same binary for comparison; the CI grep count is printed next to it.
#   2. planted bug: a copy of the tree with std::fma in the LMR table setup (make_fma_mutant.py, outside
#      forge::nnue::): v4 must FAIL with whole_text > 0 and nnue_scoped 0; v3 is expected to PASS (its scope gap).
#   3. v4 fixture tests (test_forge_sol_S05_fmacheck_v4.py) and Sol's v3 fixture runner against v3 (reference).
# usage: opus_round1/sol_S05fix/ci_s05fix.sh [out_dir]
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
JOB="$ROOT/opus_round1/sol_S05fix"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
status=0
build() {  # build <src> <dir>
  cmake -S "$1" -B "$2" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE_FLAGS" > "$OUT/configure_$(basename "$2").log" 2>&1 || exit 1
  cmake --build "$2" -j"$(nproc)" --target forge > "$OUT/build_$(basename "$2").log" 2>&1 || { tail -50 "$OUT/build_$(basename "$2").log"; exit 1; }
}
check() {  # check <exe> <tag> <expected v4 exit> <expected v3 exit>
  echo "== $2: $(sha256sum "$1" | cut -d' ' -f1)  grep count (objdump -d | grep -cE 'vfn?m(add|sub)'): $(objdump -d "$1" | grep -cE 'vfn?m(add|sub)' || true)" | tee -a "$OUT/checks.log"
  python3 -B "$JOB/forge_sol_S05_fmacheck_v4.py" "$1" > "$OUT/v4_$2.out" 2> "$OUT/v4_$2.err"; rc4=$?
  python3 -B "$JOB/sol_v3_unchanged/forge_sol_S05_fmacheck_v3_20261025.py" "$1" > "$OUT/v3_$2.out" 2> "$OUT/v3_$2.err"; rc3=$?
  echo "v4 exit $rc4 (want $3): $(head -1 "$OUT/v4_$2.out") $(cat "$OUT/v4_$2.err")" | tee -a "$OUT/checks.log"
  echo "v3 exit $rc3 (want $4): $(cut -c1-160 "$OUT/v3_$2.out") $(cat "$OUT/v3_$2.err" | cut -c1-200)" | tee -a "$OUT/checks.log"
  [ "$rc4" = "$3" ] && [ "$rc3" = "$4" ] || status=1
}
build "$ROOT" "$OUT/build_default"
check "$OUT/build_default/forge" default 0 0
mkdir -p "$OUT/mutant_src" && git -C "$ROOT" archive HEAD | tar -x -m -C "$OUT/mutant_src"
python3 -B "$JOB/make_fma_mutant.py" "$OUT/mutant_src" | tee -a "$OUT/checks.log"
build "$OUT/mutant_src" "$OUT/build_mutant"
check "$OUT/build_mutant/forge" mutant_fma_outside_nnue 1 0
grep -q 'nnue_scoped=0' "$OUT/v4_mutant_fma_outside_nnue.out" || status=1
python3 -B "$JOB/test_forge_sol_S05_fmacheck_v4.py" -v > "$OUT/v4_fixture_tests.log" 2>&1 || status=1
tail -3 "$OUT/v4_fixture_tests.log" | tee -a "$OUT/checks.log"
python3 -B "$JOB/sol_v3_unchanged/forge_sol_S05_fmacheck_tests_20261025.py" \
  --checker "$JOB/sol_v3_unchanged/forge_sol_S05_fmacheck_v3_20261025.py" --out "$OUT/v3_fixture_receipts" \
  > "$OUT/v3_fixture_tests.log" 2>&1
echo "Sol's v3 fixture runner against v3 (reference, exit $?): $(tail -1 "$OUT/v3_fixture_tests.log")" | tee -a "$OUT/checks.log"
echo "ci_s05fix status=$status" | tee -a "$OUT/checks.log"
exit $status
