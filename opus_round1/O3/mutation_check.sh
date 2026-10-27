#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that the new O3 unit tests fail.
# usage: opus_round1/O3/mutation_check.sh <scratch_dir>   (run from the repository root; needs cmake, ninja, g++)
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
mkdir -p "$SRC"
cp -a "$ROOT/." "$SRC/"
cmake -S "$SRC" -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=${CXX:-g++}" \
  "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
  ${MUTATION_LINK_FLAGS:+"-DCMAKE_EXE_LINKER_FLAGS=$MUTATION_LINK_FLAGS"} > "$SCRATCH/configure.log" 2>&1 || { cat "$SCRATCH/configure.log"; exit 1; }
status=0
mutate() { # name file python-replace(old,new) test-target
  local name=$1 file=$2 old=$3 new=$4 target=$5
  cp "$ROOT/$file" "$SRC/$file"
  python3 - "$SRC/$file" "$old" "$new" <<'EOF' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if old not in s: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
EOF
  if ! cmake --build "$BUILD" --target "$target" -j 3 > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    out=$("$BUILD/$target" 2>&1 | tail -1)
    case "$out" in
      FAIL*) echo "MUTATION $name -> caught ($out)" ;;
      *) echo "MUTATION $name -> NOT caught ($out)"; status=1 ;;
    esac
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
mutate killer_order src/search/movepicker.hpp \
  'if (!skip_quiets && is_valid_quiet(killers_[0])) return killers_[0];' \
  'if (!skip_quiets && is_valid_quiet(killers_[0])) return killers_[1];' forge_movepicker_tests
mutate see_threshold src/search/movepicker.hpp \
  'if (!board_.see_ge(move, -move_score_threshold(move))) {' \
  'if (!board_.see_ge(move, 1 - move_score_threshold(move))) {' forge_movepicker_tests
mutate check_bonus src/search/movepicker.hpp \
  'if (direct_check(move)) score += 12000;' 'if (direct_check(move)) score += 1200;' forge_movepicker_tests
mutate gravity_divisor include/forge/history.hpp \
  'entry * std::abs(clamped) / HistoryMax);' 'entry * std::abs(clamped) / (HistoryMax + 1));' forge_history_tests
mutate cont_half_ply src/search/history.inc 'back == 4 ? bonus / 2 : bonus' 'back == 2 ? bonus / 2 : bonus' forge_history_tests
mutate counter_slot src/search/history.inc \
  '[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to] = move;' \
  '[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.from] = move;' forge_history_tests
mutate soft_divisor src/search/timeman.hpp 'soft = available / tune::TmSoftDivisor' 'soft = (available - 1) / tune::TmSoftDivisor' forge_timeman_tests
mutate effort_clamp src/search/timeman.hpp 'effort, 0.6, 1.4);' 'effort, 0.6, 1.5);' forge_timeman_tests
echo "mutation_check status=$status"
exit $status
