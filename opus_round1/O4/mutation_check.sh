#!/usr/bin/env bash
# Plants one bug at a time in a scratch copy of the tree and checks that forge_pure_nnue_tests (with the engine
# for its UCI part) fails. usage (from the repository root):
#   opus_round1/O4/mutation_check.sh <scratch_dir> [mutation names...]   (default: all mutations)
# Environment: CXX (compiler), MUTATION_LINK_FLAGS (e.g. -static on MinGW), JOBS (default 1).
# The scratch copy and its build are reused by later calls, so the mutations can be run in several short parts.
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
shift
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
mkdir -p "$SRC"
cp -a "$ROOT/include" "$ROOT/src" "$ROOT/tests" "$ROOT/tools" "$ROOT/bench" "$ROOT/CMakeLists.txt" "$SRC/"
if [ ! -f "$BUILD/build.ninja" ]; then
  cmake -S "$SRC" -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=${CXX:-g++}" \
    "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
    ${MUTATION_LINK_FLAGS:+"-DCMAKE_EXE_LINKER_FLAGS=$MUTATION_LINK_FLAGS"} > "$SCRATCH/configure.log" 2>&1 || { cat "$SCRATCH/configure.log"; exit 1; }
fi
status=0
targets="--target forge --target forge_pure_nnue_tests"
run_tests() { (cd "$SCRATCH" && "$BUILD/forge_pure_nnue_tests" "$BUILD/forge" 3000 2>&1); }
# shellcheck disable=SC2086
cmake --build "$BUILD" $targets -j "${JOBS:-1}" > "$SCRATCH/build_clean.log" 2>&1 || { tail -20 "$SCRATCH/build_clean.log"; exit 1; }
echo "unmutated: $(run_tests | tail -1)"
mutate() { # name file old new
  local name=$1 file=$2 old=$3 new=$4
  if [ "${#selected[@]}" -gt 0 ] && [[ ! " ${selected[*]} " == *" $name "* ]]; then return; fi
  cp "$ROOT/$file" "$SRC/$file"
  python3 - "$SRC/$file" "$old" "$new" <<'PY' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if s.count(old) != 1: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
  # shellcheck disable=SC2086
  if ! cmake --build "$BUILD" $targets -j "${JOBS:-1}" > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    out=$(run_tests)
    fails=$(printf '%s\n' "$out" | grep -c '^FAIL' || true)
    first=$(printf '%s\n' "$out" | grep -m1 '^FAIL' | cut -c1-200 || true)
    if [ "$fails" -gt 0 ]; then echo "MUTATION $name -> caught: $fails failing checks ($(printf '%s\n' "$out" | tail -1)); first: $first"
    else echo "MUTATION $name -> NOT caught ($(printf '%s\n' "$out" | tail -1))"; status=1; fi
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
selected=("$@")
E=src/search/evaluation_v2.inc
U=src/uci.cpp
mutate residual_net_with_pure $E 'if (net != nullptr && net->residual == pure_nnue) {' 'if (false) {'
mutate standalone_net_without_pure $E 'if (net != nullptr && net->residual == pure_nnue) {' 'if (net != nullptr && net->residual == pure_nnue && pure_nnue) {'
mutate pure_alone_selects_nothing $E 'const int wanted = nnue_king_buckets > 0 ? nnue_king_buckets : (pure_nnue ? 1 : 0);' 'const int wanted = nnue_king_buckets;'
mutate pure_eval_adds_hce $E '    const bool residual = net.residual;' '    const bool residual = true;'
mutate pure_request_not_a_request $E 'if (file.empty() && nnue_king_buckets <= 0 && !pure_nnue) return {};' 'if (file.empty() && nnue_king_buckets <= 0) return {};'
mutate uci_option_ignored $U 'if (value_text == "1" || value_text == "true") forge::options::pure_nnue = true;' 'if (value_text == "1" || value_text == "true") forge::options::pure_nnue = false;'
# leave the copy unmutated and built
# shellcheck disable=SC2086
cmake --build "$BUILD" $targets -j "${JOBS:-1}" > "$SCRATCH/build_restore.log" 2>&1
echo "mutation_check status=$status"
exit $status
