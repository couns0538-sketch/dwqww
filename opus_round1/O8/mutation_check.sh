#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that tests/corr_ext_tests.cpp
# (target forge_corr_ext_tests) fails on each of them.
# usage: opus_round1/O8/mutation_check.sh <scratch_dir>   (run from the repository root; needs cmake, ninja, g++)
# env: CXX (compiler), JOBS (build jobs, default 1), PYTHON (default python3),
#      MUTATION_LINK_FLAGS (e.g. -static for MinGW so the test exe runs without DLL lookup)
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
PY=${PYTHON:-python3}
TARGET=forge_corr_ext_tests
mkdir -p "$SRC"
cp -a "$ROOT/." "$SRC/"
cmake -S "$SRC" -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=${CXX:-g++}" \
  "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
  ${MUTATION_LINK_FLAGS:+"-DCMAKE_EXE_LINKER_FLAGS=$MUTATION_LINK_FLAGS"} > "$SCRATCH/configure.log" 2>&1 || { cat "$SCRATCH/configure.log"; exit 1; }
status=0
run_test() { # prints the test's last line
  "$BUILD/$TARGET" 2>&1 | tail -1
}
# Control: the unmodified tree must pass.
if ! cmake --build "$BUILD" --target "$TARGET" -j "${JOBS:-1}" > "$SCRATCH/build_control.log" 2>&1; then
  echo "CONTROL: build failed"; tail -5 "$SCRATCH/build_control.log"; exit 1
fi
out=$(run_test)
case "$out" in
  PASS*) echo "CONTROL unmodified tree -> passes ($out)" ;;
  *) echo "CONTROL unmodified tree -> FAILS ($out)"; exit 1 ;;
esac
mutate() { # name file old new
  local name=$1 file=$2 old=$3 new=$4
  cp "$ROOT/$file" "$SRC/$file"
  "$PY" - "$SRC/$file" "$old" "$new" <<'EOF' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if s.count(old) != 1: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
EOF
  if ! cmake --build "$BUILD" --target "$TARGET" -j "${JOBS:-1}" > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    out=$(run_test)
    case "$out" in
      FAIL*) echo "MUTATION $name -> caught ($out)" ;;
      *) echo "MUTATION $name -> NOT caught ($out)"; status=1 ;;
    esac
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
H=include/forge/corr_ext.hpp
A=src/search/alphabeta.inc
# Decision rule and budget (forge/corr_ext.hpp).
mutate triple_room_off_by_one $H 'if (room >= 2 && triple_allowed(correction)' 'if (room >= 1 && triple_allowed(correction)'
mutate double_room_off_by_one $H 'if (room >= 1 && singular_score < singular_beta - double_margin(correction)) return 2;' \
  'if (room >= 0 && singular_score < singular_beta - double_margin(correction)) return 2;'
mutate budget_ignored $H 'const int room = tune::CorrExtBudget - path_extra;' 'const int room = tune::CorrExtBudget + 0 * path_extra;'
mutate path_triple_counts_one $H 'return path_extra + std::max(0, extension - 1);' 'return path_extra + (extension >= 2);'
mutate path_counts_negative $H 'return path_extra + std::max(0, extension - 1);' 'return path_extra + extension - 1;'
mutate double_margin_sign $H 'return std::max(0, 24 - correction * tune::CorrExtDoublePct / 100);' \
  'return std::max(0, 24 + correction * tune::CorrExtDoublePct / 100);'
mutate double_margin_lock_constant $H 'return std::max(0, 24 - correction' 'return std::max(0, 25 - correction'
mutate double_margin_no_floor $H 'return std::max(0, 24 - correction * tune::CorrExtDoublePct / 100);' \
  'return 24 - correction * tune::CorrExtDoublePct / 100;'
mutate triple_threshold_ignored $H 'return tune::CorrExtTripleCorr > 0 && correction >= tune::CorrExtTripleCorr;' \
  'return tune::CorrExtTripleCorr > 0;'
mutate triple_threshold_strict $H 'correction >= tune::CorrExtTripleCorr;' 'correction > tune::CorrExtTripleCorr;'
mutate triple_margin_inclusive $H 'singular_score < singular_beta - tune::CorrExtTripleMargin) return 3;' \
  'singular_score <= singular_beta - tune::CorrExtTripleMargin) return 3;'
mutate pv_not_excluded $H 'if (pv_node) return 1;' 'if (pv_node && singular_score > singular_beta) return 1;'
mutate correction_in_check $H 'if (in_check || static_eval == ValueNone' 'if (static_eval == ValueNone'
# The CorrExt search instance (src/search/alphabeta.inc, second inclusion).
mutate search_lock_accounting $A 'ss->double_extensions = corr_ext::path_extra_after(inherited_double_extensions, extension);' \
  'ss->double_extensions = inherited_double_extensions + (extension == 2);'
mutate search_correction_zero $A 'const int correction = corr_ext::correction_size(in_check, ss->static_eval, ss->raw_eval);' \
  'const int correction = 0 * corr_ext::correction_size(in_check, ss->static_eval, ss->raw_eval);'
mutate search_budget_from_root $A 'extension = corr_ext::singular_extension(pv_node, singular_score, singular_beta, correction,' \
  'extension = corr_ext::singular_extension(pv_node, singular_score, singular_beta, correction, 0 *'
mutate search_lmp_copy_differs src/search/corr_ext.inc '(tune::LmpBase + depth * depth) / 2;' '(tune::LmpBase + depth * depth) / 3;'
# Root dispatch (src/search/iterative.inc).
mutate dispatch_ignored src/search/iterative.inc 'options::corr_ext != 0 ? search_corr_ext(' 'false ? search_corr_ext('
mutate dispatch_inverted src/search/iterative.inc 'options::corr_ext != 0 ? search_corr_ext(' 'options::corr_ext == 0 ? search_corr_ext('
echo "mutation_check status=$status"
exit $status
