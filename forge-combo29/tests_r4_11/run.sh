#!/usr/bin/env bash
# Build tests_r4_11/r4_11_test with address and undefined sanitizers.
# CMakeLists.txt is not modified. No FORGE_* cache variable is passed, so the
# lock defaults in CMakeLists.txt stay as they are. A failed compile, a failed
# check, or a sanitizer finding exits non-zero.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
build="${TMPDIR:-/tmp}/r4_11_asan"
mkdir -p "$build"

# g++ is the compiler from the finding-11 proof. /usr/bin/c++ on this image is
# Clang without its sanitizer runtime, so the lock file is configured with g++.
cmake -S "$root" -B "$build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER=g++ \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DCMAKE_CXX_FLAGS="-g -fsanitize=address,undefined -fno-sanitize-recover=address,undefined -fno-omit-frame-pointer" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=address,undefined"
cmake --build "$build" -j "$(nproc)"

mapfile -t cmd < <(python3 - "$build/compile_commands.json" "$root/tests_r4_11/r4_11_test.cpp" "$build/r4_11_test.cpp.o" <<'PY'
import json, shlex, sys
cc_path, src, obj = sys.argv[1:]
entries = json.load(open(cc_path))
entry = next(e for e in entries if e["file"].endswith("src/eval_params.cpp"))
argv = shlex.split(entry["command"]) if "command" in entry else list(entry["arguments"])
out = []
i = 0
while i < len(argv):
    if argv[i] == "-o" and i + 1 < len(argv):
        out.extend(["-o", obj])
        i += 2
        continue
    if argv[i].endswith("eval_params.cpp"):
        out.append(src)
        i += 1
        continue
    out.append(argv[i])
    i += 1
print("\n".join(out))
PY
)
"${cmd[@]}"

objects=()
while IFS= read -r obj; do
    objects+=("$obj")
done < <(find "$build/CMakeFiles/forge.dir/src" -name '*.cpp.o' ! -name 'uci.cpp.o' | sort)

"${cmd[0]}" -fsanitize=address,undefined -fno-sanitize-recover=address,undefined \
    "$build/r4_11_test.cpp.o" "${objects[@]}" -pthread -o "$build/r4_11_test"

export ASAN_OPTIONS="${ASAN_OPTIONS:-abort_on_error=1:halt_on_error=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-abort_on_error=1:halt_on_error=1}"
"$build/r4_11_test"
