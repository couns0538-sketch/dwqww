#!/usr/bin/env bash
# toolchain_pins.sh : build the SAME unmodified 6b98f217 source with several g++ versions and print the four
# honesty numbers for each. Answers: does the node-count pin depend on the libstdc++ version?
#
# For each compiler: fresh build directory, same CMake release flags, then one fresh engine process per
# honesty line, raw output kept under the build's own folder. Nothing is patched or edited.
set -u
SRC="${1:?source tree}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
shift 2
for CXX in "$@"; do
  TAG="$(echo "$CXX" | tr -d '+')"
  BD="$OUT/build_$TAG"
  rm -rf "$BD"
  {
    echo "compiler: $CXX"
    "$CXX" --version | head -1
    echo "source: $SRC (pristine, unmodified)"
  } > "$OUT/meta_$TAG.txt"
  if ! cmake -S "$SRC" -B "$BD" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" \
        >> "$OUT/meta_$TAG.txt" 2>&1; then
    echo "$TAG BUILD FAILED (cmake); see meta_$TAG.txt"
    continue
  fi
  if ! make -C "$BD" -j4 >> "$OUT/meta_$TAG.txt" 2>&1; then
    echo "$TAG BUILD FAILED (make); see meta_$TAG.txt"
    continue
  fi
  EXE="$BD/forge"
  {
    echo "exe $EXE"
    sha256sum "$EXE"
    printf 'uci\nquit\n' | "$EXE" 2>&1 | tr -d '\r' | grep -E '^id name|^info string.*(compiler|version)' || true
    echo "libstdc++: $(ldd "$EXE" | grep -i libstdc | sed 's/.*=> //;s/ (.*//')"
    "$CXX" -dumpfullversion
  } >> "$OUT/meta_$TAG.txt"
  for d in 11 13 16; do
    printf 'bench %s\nquit\n' "$d" | "$EXE" 2>&1 | tr -d '\r' > "$OUT/bench_${d}_$TAG.txt"
  done
  printf 'go perft 5\nquit\n' | "$EXE" 2>&1 | tr -d '\r' > "$OUT/perft5_$TAG.txt"
  b11=$(grep -o 'bench depth 11 nodes [0-9]*' "$OUT/bench_11_$TAG.txt" | sed 's/.*nodes //')
  b13=$(grep -o 'bench depth 13 nodes [0-9]*' "$OUT/bench_13_$TAG.txt" | sed 's/.*nodes //')
  b16=$(grep -o 'bench depth 16 nodes [0-9]*' "$OUT/bench_16_$TAG.txt" | sed 's/.*nodes //')
  pf=$(grep -E '^nodes [0-9]+$' "$OUT/perft5_$TAG.txt" | sed 's/nodes //')
  echo "$TAG: bench11=${b11:-MISSING} bench13=${b13:-MISSING} bench16=${b16:-MISSING} perft5=${pf:-MISSING}"
  date -u
done
