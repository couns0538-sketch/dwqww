#!/usr/bin/env bash
# Run on a disposable Linux Git checkout, never on the frozen release source.
set -euo pipefail
if [ "$#" -ne 1 ]; then echo "Usage: $0 RESULTS_DIR" >&2; exit 2; fi
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
OUTPUT="$1"
mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"
if [ -n "$(find "$OUTPUT" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  echo "Refusing to overwrite pre-existing evidence in $OUTPUT" >&2
  exit 2
fi
TEMP="$(mktemp -d)"
trap 'printf "temporary checkout: %s\n" "$TEMP" >&2' EXIT
mkdir -p "$TEMP/baseline" "$TEMP/candidate"
SOURCE_REV="$(git -C "$REPO" rev-parse HEAD)"
printf 'Source commit: %s\n' "$SOURCE_REV" > "$OUTPUT/identities.txt"
printf 'Build platform: Linux %s\n' "$(uname -m)" >> "$OUTPUT/identities.txt"
printf 'Compiler: %s\n' "$(g++ -dumpfullversion -dumpversion)" >> "$OUTPUT/identities.txt"
sha256sum "$HERE/uci-clock-origin-scoped.patch" "$REPO/src/nnue_weights.inc" >> "$OUTPUT/identities.txt"
(git -C "$REPO" archive "$SOURCE_REV") | tar -x -C "$TEMP/baseline"
(git -C "$REPO" archive "$SOURCE_REV") | tar -x -C "$TEMP/candidate"
(cd "$TEMP/candidate" && git apply --check "$HERE/uci-clock-origin-scoped.patch" && git apply "$HERE/uci-clock-origin-scoped.patch")
printf 'Patch applied to disposable candidate tree; immutable baseline untouched\n' >> "$OUTPUT/identities.txt"
logged() {
  local name="$1"; shift
  "$@" > "$OUTPUT/$name.stdout" 2> "$OUTPUT/$name.stderr"
}
logged base_config cmake -S "$TEMP/baseline" -B "$TEMP/basebuild" -DCMAKE_BUILD_TYPE=Release -DFORGE_NATIVE=OFF
logged base_build cmake --build "$TEMP/basebuild" --parallel 2
logged base_ctest ctest --test-dir "$TEMP/basebuild" --output-on-failure -j 1
logged candidate_config cmake -S "$TEMP/candidate" -B "$TEMP/candbuild" -DCMAKE_BUILD_TYPE=Release -DFORGE_NATIVE=OFF
logged candidate_build cmake --build "$TEMP/candbuild" --parallel 2
logged candidate_ctest ctest --test-dir "$TEMP/candbuild" --output-on-failure -j 1
logged shim_build cc -std=gnu11 -O2 -fPIC -shared -Wall -Wextra -Werror -o "$TEMP/libdelay.so" "$HERE/delayed_pthread_create.c" -ldl
sha256sum "$TEMP/basebuild/forge" "$TEMP/candbuild/forge" "$TEMP/libdelay.so" >> "$OUTPUT/identities.txt"
logged probe python3 "$HERE/native_clock_probe.py" --baseline "$TEMP/basebuild/forge" --candidate "$TEMP/candbuild/forge" --shim "$TEMP/libdelay.so" --out "$OUTPUT/probe"
printf 'PASS: full CMake/CTest and native clock-origin probe\n' > "$OUTPUT/CONCLUSION.txt"
