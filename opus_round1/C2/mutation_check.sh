#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that
# tests/correction_history_tests.cpp fails (exit != 0) for every planted bug.
# Covers the acceptance items "index / clamp / decay tests that FAIL on a planted
# off-by-one" plus the key, frame, twin and clear rules of CorrHistPlus.
# usage: opus_round1/C2/mutation_check.sh <scratch_dir>   (run from the repository root)
# env:   CXX (default g++), PYTHON (default python3), MUTATION_FLAGS (extra flags, e.g. -static on MinGW)
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
SRC="$SCRATCH/src_copy"
mkdir -p "$SRC"
cp -a "$ROOT/src" "$ROOT/include" "$ROOT/tests" "$SRC/"
CXX=${CXX:-g++}
PYTHON=${PYTHON:-python3}
run_test() { # name -> builds and runs the test on the current scratch tree; prints "<exit> <summary> | <first FAIL>"
  local name=$1
  if ! (cd "$SRC" && $CXX -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math \
        -march=x86-64-v3 -pthread ${MUTATION_FLAGS:-} -Iinclude -Isrc src/bitboard.cpp src/board.cpp src/book.cpp \
        src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp tests/correction_history_tests.cpp \
        -o "$SCRATCH/cht_$name") > "$SCRATCH/build_$name.log" 2>&1; then
    echo "BUILD-FAILED"; tail -5 "$SCRATCH/build_$name.log"; return
  fi
  "$SCRATCH/cht_$name" > "$SCRATCH/run_$name.log" 2>&1
  echo "$? $(grep '^SUMMARY' "$SCRATCH/run_$name.log" | tail -1) | $(grep -m1 '^FAIL ' "$SCRATCH/run_$name.log")"
}
status=0
result=$(run_test baseline)
echo "BASELINE (unmutated): $result"
case "$result" in "0 SUMMARY"*) ;; *) echo "baseline must pass before mutating"; exit 1 ;; esac
mutate() { # name file old new
  local name=$1 file=$2 old=$3 new=$4
  cp "$ROOT/$file" "$SRC/$file"
  if ! "$PYTHON" - "$SRC/$file" "$old" "$new" <<'EOF'
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if s.count(old) != 1: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
EOF
  then echo "MUTATION $name: pattern not found exactly once"; status=1; return; fi
  local result
  result=$(run_test "$name")
  case "$result" in
    "0 "*) echo "MUTATION $name -> NOT caught ($result)"; status=1 ;;
    BUILD-FAILED*) echo "MUTATION $name -> build failed"; status=1 ;;
    *) echo "MUTATION $name -> caught (exit $result)" ;;
  esac
  cp "$ROOT/$file" "$SRC/$file"
}
H=include/forge/correction_plus.hpp
# index: off-by-one in a stride and in the piece-type offset
mutate index_stride_63 $H 'index = index * 64 + static_cast<std::size_t>(our_to);' 'index = index * 63 + static_cast<std::size_t>(our_to);'
mutate index_type_offset $H 'static_cast<std::size_t>(their_type - 1);' 'static_cast<std::size_t>(their_type);'
# clamp: entry clamp and blend clamp one below the limit
mutate clamp_limit_minus1 $H 'div_pow2<13>(entry * magnitude), -CorrectionLimit, CorrectionLimit);' 'div_pow2<13>(entry * magnitude), -CorrectionLimit, CorrectionLimit - 1);'
mutate total_limit_minus1 $H 'constexpr int TotalLimit = 2 * CorrectionLimit;' 'constexpr int TotalLimit = 2 * CorrectionLimit - 1;'
# decay: divisor off by one in both directions
mutate decay_shift_minus1 $H 'div_pow2<13>(entry * magnitude)' 'div_pow2<12>(entry * magnitude)'
mutate decay_shift_plus1 $H 'div_pow2<13>(entry * magnitude)' 'div_pow2<14>(entry * magnitude)'
mutate div_pow2_bias_plus1 $H 'return (x + ((x >> 31) & ((1 << Shift) - 1))) >> Shift;' 'return (x + ((x >> 31) & (1 << Shift))) >> Shift;'
mutate div_pow2_floor $H 'return (x + ((x >> 31) & ((1 << Shift) - 1))) >> Shift;' 'return x >> Shift;'
mutate div100_rounding $H 'return static_cast<int>(scaled >> 37) + (x < 0 ? 1 : 0);' 'return static_cast<int>(scaled >> 37);'
# step: depth weight off by one
mutate step_depth_weight $H 'return div_pow2<8>(residual * std::min(depth + 1, 16));' 'return div_pow2<8>(residual * std::min(depth, 16));'
# keys: the minor key forgets the white king
mutate minor_key_no_white_king $H 'board.pieces(WK) * KeyMultipliers[4] + ' ''
# search glue: frame one ply off, twin drifting from the lock update, clear() keeping the tables
mutate frame_offset src/search/correction_plus.inc 'const SearchStack* ss = &stack_[4 + ply];' 'const SearchStack* ss = &stack_[3 + ply];'
# (a twin divisor 255 instead of 256 would be an equivalent mutant: diff is a multiple of 256 clipped to
#  +-2048, so diff * weight / 255 == diff * weight / 256 for every reachable input)
mutate twin_depth_cap src/search/correction_plus.inc 'const int weight = std::min(depth + 1, 16);' 'const int weight = std::min(depth + 1, 15);'
mutate clear_keeps_tables src/search/worker.inc 'correction_plus_.reset();' ''
echo "mutation_check status=$status"
exit $status
