#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that tests/corr_margins_tests.cpp
# (target forge_corr_margins_tests) fails on each of them.
# usage: opus_round1/O5/mutation_check.sh <scratch_dir>   (run from the repository root; needs cmake, ninja, g++)
# env: CXX (compiler), JOBS (build jobs, default 1), PYTHON (default python3),
#      MUTATION_LINK_FLAGS (e.g. -static for MinGW so the test exe runs without DLL lookup)
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
PY=${PYTHON:-python3}
TARGET=forge_corr_margins_tests
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
H=include/forge/corr_margins.hpp
A=src/search/alphabeta.inc
# Margin functions (forge/corr_margins.hpp).
mutate rfp_sign $H 'improving + correction * tune::CorrRfpPct / 100;' 'improving - correction * tune::CorrRfpPct / 100;'
mutate rfp_lock_offset $H 'return tune::RfpMargin * depth - tune::RfpImproving * improving +' \
  'return 1 + tune::RfpMargin * depth - tune::RfpImproving * improving +'
mutate futility_wrong_weight $H 'correction * tune::CorrFutilityPct / 100;' 'correction * tune::CorrRfpPct / 100;'
mutate futility_sign $H 'lmr_depth + correction * tune::CorrFutilityPct / 100;' 'lmr_depth - correction * tune::CorrFutilityPct / 100;'
mutate null_move_lock_constant $H 'return beta - 24 * depth + 180 +' 'return beta - 24 * depth + 181 +'
mutate null_move_sign $H '180 + correction * tune::CorrNullMovePct / 100;' '180 - correction * tune::CorrNullMovePct / 100;'
mutate lmr_no_cap $H 'return r - std::min(r, r * correction * tune::CorrLmrPct / 6400);' \
  'return r - r * correction * tune::CorrLmrPct / 6400;'
mutate lmr_touches_nonpositive $H 'if (r <= 0) return r;' 'if (r < 0) return r - 1;'
mutate lmr_scale $H 'tune::CorrLmrPct / 6400);' 'tune::CorrLmrPct / 3200);'
mutate correction_in_check $H 'if (in_check || static_eval == ValueNone' 'if (static_eval == ValueNone'
mutate correction_signed $H 'return std::abs(static_eval - raw_eval);' 'return static_eval - raw_eval;'
# The CorrMargins search instance (src/search/alphabeta.inc, second inclusion).
mutate search_rfp_lock_formula $A 'eval - corr_margins::rfp_margin(depth, improving, correction) >= beta' \
  'eval - corr_margins::rfp_margin(depth, improving, 0) >= beta'
mutate search_null_move_lock_formula $A 'corr_margins::null_move_threshold(beta, depth, correction)' \
  'corr_margins::null_move_threshold(beta, depth, 0)'
mutate search_futility_lock_formula $A 'corr_margins::futility_margin(lmr_depth, correction)' \
  'corr_margins::futility_margin(lmr_depth, 0)'
mutate search_lmr_skipped $A 'r = corr_margins::lmr_reduction(r, correction);' '(void)correction;'
mutate search_correction_zero $A 'const int correction = corr_margins::correction_size(in_check, ss->static_eval, ss->raw_eval);' \
  'const int correction = 0 * corr_margins::correction_size(in_check, ss->static_eval, ss->raw_eval);'
mutate search_lmp_copy_differs src/search/corr_margins.inc '(tune::LmpBase + depth * depth) / 2;' '(tune::LmpBase + depth * depth) / 3;'
mutate search_lmr_relief_on_all $A 'r = corr_margins::lmr_reduction(r, correction);' 'r = corr_margins::lmr_reduction(r, correction) - (r > 6);'
# Root dispatch (src/search/iterative.inc).
mutate dispatch_ignored src/search/iterative.inc 'options::corr_margins != 0 ? search_corr_margins(' 'false ? search_corr_margins('
mutate dispatch_inverted src/search/iterative.inc 'options::corr_margins != 0 ? search_corr_margins(' 'options::corr_margins == 0 ? search_corr_margins('
echo "mutation_check status=$status"
exit $status
