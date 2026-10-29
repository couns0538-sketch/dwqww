#!/usr/bin/env bash
# R5B M4(c), Linux CI (ubuntu-24.04, g++-14, valgrind): uninitialised-read checks for the N2 build
# (-DFORGE_NNUE_O2=ON -DFORGE_NOZERO_MOVE_BUFFERS=ON -DFORGE_SPEEDSTACK=ON). ASan/UBSan (opus-r5b-n2.yml, asan job)
# catch out-of-bounds and UB but not reads of uninitialised memory, which is the NOZERO risk; this script adds:
#   1. valgrind memcheck (--track-origins=yes) on the engine of OFF (control) and N2: bench 11, perft 4, and
#      go depth 10 on four positions with castling / en passant / promotions; any memcheck error fails;
#   2. N2 built with -ftrivial-auto-var-init=pattern and with =zero: the lock identity (bench d11-d22 + perft, the
#      MovePicker / MoveList buffers are stack locals, so a read of an unwritten entry would change the nodes).
# usage: opus_r5/r5b/ci_n2_memcheck.sh [out_dir]      exit 0 = all checks pass
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
BASE="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
N2="-DFORGE_NNUE_O2=ON -DFORGE_NOZERO_MOVE_BUFFERS=ON -DFORGE_SPEEDSTACK=ON"
status=0
build() {  # build <name> <build type> <extra cxx flags> [cmake -D switches...]
  local name=$1 type=$2 extra=$3; shift 3
  # shellcheck disable=SC2068
  cmake -S "$ROOT" -B "$OUT/build_$name" -G Ninja -DCMAKE_BUILD_TYPE="$type" -DCMAKE_CXX_COMPILER="$CXX" \
    "-DCMAKE_CXX_FLAGS=$BASE $extra" $@ > "$OUT/configure_$name.log" 2>&1 || { tail -30 "$OUT/configure_$name.log"; exit 1; }
  cmake --build "$OUT/build_$name" --target forge -j"$(nproc)" > "$OUT/build_$name.log" 2>&1 || { tail -50 "$OUT/build_$name.log"; exit 1; }
  echo "build $name: $type [$BASE $extra] $* sha256 $(sha256sum "$OUT/build_$name/forge" | cut -d' ' -f1)" \
    "FMA $(objdump -d "$OUT/build_$name/forge" | grep -cE 'vfn?m(add|sub)' || true)" | tee -a "$OUT/memcheck_builds.log"
}
echo "compiler: $($CXX --version | head -1); valgrind: $(valgrind --version)" | tee "$OUT/memcheck_builds.log"
lscpu | grep -E 'Model name' | tee -a "$OUT/memcheck_builds.log"

# 1. valgrind memcheck, OFF (control) and N2, RelWithDebInfo (-O2 -g) for source lines in the reports
build off_dbg RelWithDebInfo ""
# shellcheck disable=SC2086
build n2_dbg RelWithDebInfo "" $N2
for name in off_dbg n2_dbg; do
  log="$OUT/memcheck_$name.log"
  python3 "$ROOT/opus_r5/r5b/ci_uci_script.py" --log "$log" -- valgrind --tool=memcheck --track-origins=yes \
    --error-exitcode=99 "--log-file=$OUT/valgrind_$name.txt" "$OUT/build_$name/forge" > "$OUT/memcheck_${name}_uci.log" 2>&1
  rc=$?
  errors=$(grep -E 'ERROR SUMMARY' "$OUT/valgrind_$name.txt" | tail -1)
  echo "memcheck $name: exit $rc, $errors" | tee -a "$OUT/memcheck_summary.log"
  if [ "$rc" -ne 0 ] || ! grep -q 'ERROR SUMMARY: 0 errors' "$OUT/valgrind_$name.txt"; then
    status=1; grep -E 'uninitialised|Invalid|at 0x|by 0x' "$OUT/valgrind_$name.txt" | head -60
  fi
done

# 2. N2 with pattern / zero initialisation of every automatic variable: the lock pins must still hold
for init in pattern zero; do
  # shellcheck disable=SC2086
  build "n2_init_$init" Release "-ftrivial-auto-var-init=$init" $N2
  python3 "$ROOT/opus_round1/ci/uci_check.py" "$OUT/build_n2_init_$init/forge" --full 2>&1 | tee "$OUT/identity_n2_init_$init.log"
  if ! grep -q '^ALL OK' "$OUT/identity_n2_init_$init.log"; then status=1; fi
  echo "N2 -ftrivial-auto-var-init=$init identity: $(tail -1 "$OUT/identity_n2_init_$init.log")" | tee -a "$OUT/memcheck_summary.log"
done
echo "ci_n2_memcheck status=$status" | tee -a "$OUT/memcheck_summary.log"
exit $status
