#!/usr/bin/env bash
# Planted-bug check for the fail-loud review fix (loader size check, no net after a failed load, the request
# rule and its UCI side): plants one bug at a time in a scratch copy of the tree, rebuilds forge,
# forge_nnue_v2_tests and forge_nnue_v2_uci_tests, and checks that at least one of the two test programs fails.
# usage: opus_round1/C4/mutation_check_failloud.sh <scratch_dir>   (run from the repository root; cmake, ninja, g++)
# Environment: CXX (compiler), MUTATION_LINK_FLAGS (e.g. -static on MinGW), JOBS (default 1).
set -uo pipefail
ROOT=$(pwd)
SCRATCH=$1
SRC="$SCRATCH/src_copy"
BUILD="$SCRATCH/build"
RUN="$SCRATCH/run"
mkdir -p "$SRC" "$RUN"
cp -a "$ROOT/." "$SRC/"
cmake -S "$SRC" -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=${CXX:-g++}" \
  "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
  ${MUTATION_LINK_FLAGS:+"-DCMAKE_EXE_LINKER_FLAGS=$MUTATION_LINK_FLAGS"} > "$SCRATCH/configure.log" 2>&1 || { cat "$SCRATCH/configure.log"; exit 1; }
TARGETS="--target forge --target forge_nnue_v2_tests --target forge_nnue_v2_uci_tests"
ENGINE="$BUILD/forge"
[ -f "$BUILD/forge.exe" ] && ENGINE="$BUILD/forge.exe"
status=0
# shellcheck disable=SC2086
cmake --build "$BUILD" $TARGETS -j "${JOBS:-1}" > "$SCRATCH/build_clean.log" 2>&1 || { tail -20 "$SCRATCH/build_clean.log"; exit 1; }
tests() { # prints "<unit summary> | <uci summary>" and the failing lines to $RUN/last.log
  (cd "$RUN" && "$BUILD/forge_nnue_v2_tests" 4000 > unit.log 2>&1; "$BUILD/forge_nnue_v2_uci_tests" "$ENGINE" > uci.log 2>&1)
  echo "unit $(tail -1 "$RUN/unit.log") | uci $(tail -1 "$RUN/uci.log")"
}
echo "unmutated: $(tests)"
mutate() { # name file occurrence old new  (replaces the occurrence-th match of old, 1-based)
  local name=$1 file=$2 nth=$3 old=$4 new=$5
  cp "$ROOT/$file" "$SRC/$file"
  python3 - "$SRC/$file" "$nth" "$old" "$new" <<'PY' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, nth, old, new = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
s = open(path, encoding="utf-8").read()
at = -1
for _ in range(nth):
    at = s.find(old, at + 1)
    if at < 0:
        sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s[:at] + new + s[at + len(old):])
PY
  # shellcheck disable=SC2086
  if ! cmake --build "$BUILD" $TARGETS -j "${JOBS:-1}" > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    summary=$(tests)
    fails=$(cat "$RUN/unit.log" "$RUN/uci.log" | grep -c '^FAIL' || true)
    first=$(cat "$RUN/unit.log" "$RUN/uci.log" | grep -m1 '^FAIL' | cut -c1-200 || true)
    if [ "$fails" -gt 0 ]; then echo "MUTATION $name -> caught: $fails failing checks ($summary); first: $first"
    else echo "MUTATION $name -> NOT caught ($summary)"; status=1; fi
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
N=src/nnue.cpp
E=src/search/evaluation_v2.inc
U=src/uci.cpp
UNUSABLE='if (nnue_v2_unusable()) { exit_status = NnueV2ExitStatus; break; }'
# loader
mutate keep_previous_net_on_failure $N 1 '    unload();
    last_bytes_read = 0;' '    last_bytes_read = 0;'
mutate weights_read_before_size_check $N 1 '    if (size != expected) {' '    if (false) {'
mutate no_too_large_check $N 1 '    if (size > largest) {' '    if (false) {'
# request rule
mutate usennue_false_is_an_error $E 1 '    if (!nnue::enabled) return {};   // UseNNUE false: every network off on purpose' ''
mutate file_with_buckets_0_is_fine $E 1 '    if (nnue_king_buckets <= 0) {
        return "NNUEFile "' '    if (nnue_king_buckets <= 0) {
        if (true) return {};
        return "NNUEFile "'
mutate silent_fallback_on_mismatch $E 1 '    return "NNUEKingBuckets " + std::to_string(nnue_king_buckets) + " does not match NNUEFile "' '    if (true) return {};
    return "NNUEKingBuckets " + std::to_string(nnue_king_buckets) + " does not match NNUEFile "'
mutate failed_load_is_fine $E 1 'if (!file.empty() && !load_error.empty()) return' 'if (false) return'
# UCI layer
mutate isready_no_exit $U 1 "$UNUSABLE" '(void)0;'
mutate go_no_exit $U 2 "$UNUSABLE" '(void)0;'
mutate bench_no_exit $U 3 "$UNUSABLE" '(void)0;'
mutate exit_status_0 $U 1 '    return exit_status;' '    return 0;'
mutate no_active_line_at_isready $U 1 "if (!nnue_v2_active.empty()) std::cout << \"info string NNUE v2: \" << nnue_v2_active << '\\n';" '(void)0;'
mutate no_error_at_once $U 1 'if (!problem.empty()) std::cout << "info string ERROR NNUE v2: " << problem << std::endl;
            else if (active' 'if (false) (void)0;
            else if (active'
echo "mutation_check_failloud status=$status"
exit $status
