#!/usr/bin/env bash
# Plants one output-bucket bug at a time in a scratch copy of the tree and checks that forge_nnue_v2_tests fails.
# usage: opus_round1/C5/mutation_check.sh <scratch_dir>   (run from the repository root; needs cmake, ninja, g++)
# Environment: CXX (compiler), MUTATION_LINK_FLAGS (e.g. -static on MinGW), JOBS (default 1).
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
target=forge_nnue_v2_tests
cmake --build "$BUILD" --target "$target" -j "${JOBS:-1}" > "$SCRATCH/build_clean.log" 2>&1 || { tail -20 "$SCRATCH/build_clean.log"; exit 1; }
clean=$("$BUILD/$target" 4000 2>&1 | tail -1)
echo "unmutated: $clean"
mutate() { # name file old new
  local name=$1 file=$2 old=$3 new=$4
  cp "$ROOT/$file" "$SRC/$file"
  python3 - "$SRC/$file" "$old" "$new" <<'PY' || { echo "MUTATION $name: pattern not found"; status=1; return; }
import sys
path, old, new = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
if s.count(old) != 1: sys.exit(1)
open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
  if ! cmake --build "$BUILD" --target "$target" -j "${JOBS:-1}" > "$SCRATCH/build_$name.log" 2>&1; then
    echo "MUTATION $name: build failed"; tail -5 "$SCRATCH/build_$name.log"; status=1
  else
    out=$("$BUILD/$target" 4000 2>&1)
    last=$(printf '%s\n' "$out" | tail -1)
    fails=$(printf '%s\n' "$out" | grep -c '^FAIL' || true)
    first=$(printf '%s\n' "$out" | grep -m1 '^FAIL' || true)
    if [ "$fails" -gt 0 ]; then echo "MUTATION $name -> caught: $fails failing checks ($last); first: $first"
    else echo "MUTATION $name -> NOT caught ($last)"; status=1; fi
  fi
  cp "$ROOT/$file" "$SRC/$file"
}
H=include/forge/nnue_v2.hpp
mutate bucket_off_by_one $H 'std::min(popcount(board.occupied()), 32))];' 'std::min(popcount(board.occupied()) - 1, 32))];'
mutate bias_of_head_0 $H 'float out = net.b2[bucket];' 'float out = net.b2[0];'
mutate row_half_offset $H 'net.w2.data() + bucket * 2U * HiddenSize;' 'net.w2.data() + bucket * HiddenSize;'
mutate rows_ignored $H 'const std::size_t bucket = static_cast<std::size_t>(output_bucket(net, board));' 'const std::size_t bucket = 0;'
mutate select_ignores_heads src/nnue.cpp '} else if (output_buckets > 0 ? loaded_net->output_buckets != output_buckets : loaded_net->output_buckets != 1) {' '} else if (false) {'
mutate max_heads_15 $H 'constexpr int MaxOutputBuckets = 16;' 'constexpr int MaxOutputBuckets = 15;'
mutate rule_ignores_output_buckets src/search/evaluation_v2.inc 'if (file.empty() && kb <= 0 && ob <= 0) return {};' 'if (file.empty() && kb <= 0) return {};'
mutate rule_output_count_unchecked src/nnue.cpp '} else if (output_buckets > 0 ? loaded_net->output_buckets != output_buckets : loaded_net->output_buckets != 1) {' '} else if (output_buckets > 0 && loaded_net->output_buckets != output_buckets) {'
echo "mutation_check status=$status"
exit $status
