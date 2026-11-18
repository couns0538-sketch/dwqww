#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job23
job=forge-combo29/sol3/job23
base=/workspace/work/sol3-job12/tree_F
plain=/workspace/work/sol3-job12/build_F
overlay=$(realpath forge-combo29/sol3/job22/build)
cmake=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
weights=$base/src/nnue_weights.inc
flags=$(sed -n 's/^CMAKE_CXX_FLAGS:STRING=//p' "$plain/CMakeCache.txt")
[[ "$flags" == *"-march=x86-64-v4"* ]]

for label in "$@"; do
  source="$root/source/$label"
  build="$root/build/$label"
  logs="$root/build_logs/$label"
  mkdir -p "$root/source" "$root/build" "$root/build_logs"
  mkdir "$source" "$logs"
  cp -a "$base/." "$source/"
  (
    cd "$source"
    patch --batch --forward --fuzz=0 -p1 < "/workspace/work/forge-sol3/$job/step2/A-kF.patch.txt"
    if [[ "$label" == A-wrong ]]; then
      patch --batch --forward --fuzz=0 -p1 < "/workspace/work/forge-sol3/$job/step2/A-wrong.patch.txt"
    fi
  ) > "$logs/patch.txt" 2>&1
  configure=(
    "$cmake" -S "$source" -B "$build" -G "Unix Makefiles"
    -DCMAKE_CXX_COMPILER=/usr/bin/c++ -DCMAKE_BUILD_TYPE=Release
    "-DCMAKE_CXX_FLAGS:STRING=$flags" "-DCMAKE_CXX_FLAGS_RELEASE:STRING="
    "-DCMAKE_PROJECT_INCLUDE=$overlay/sanitizer_flags.cmake" -DJOB22_SANITIZER=AU
    -DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4 -DFORGE_NNUE_HIDDEN=256
    "-DFORGE_NNUE_WEIGHTS=$weights" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
  )
  compile=("$cmake" --build "$build" --target forge --parallel 2 --verbose)
  {
    date -u +%FT%TZ
    /usr/bin/c++ --version
    "$cmake" --version
    printf '%q ' "${configure[@]}"
    printf '\n'
    printf '%q ' "${compile[@]}"
    printf '\n'
  } > "$logs/commands.txt"
  env -u CXXFLAGS -u CPPFLAGS -u CFLAGS -u LDFLAGS "${configure[@]}" > "$logs/configure.txt" 2>&1
  python3 -B "$overlay/verify_flags.py" AU "$plain" "$build" > "$logs/flags.txt"
  cp "$build/CMakeFiles/forge.dir/link.txt" "$logs/link.txt"
  "${compile[@]}" > "$logs/build.txt" 2>&1
  {
    sha256sum "$build/forge"
    date -u +%FT%TZ
    printf '%s\n' 'build exit 0'
  } > "$logs/result.txt"
done
