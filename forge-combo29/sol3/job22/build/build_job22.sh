#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cmake=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
r15d=/workspace/work/sol3-job4/r15d
kf=/workspace/work/sol3-job12/tree_F
plain_r15d=/workspace/work/sol3-job4/build_0
plain_kf=/workspace/work/sol3-job12/build_F

if [[ "$#" -eq 0 ]]; then
  set -- T-r15d C-T AU-r15d T-kF C-AU AU-kF C-UB
fi
for tag in "$@"; do
  case "$tag" in
    AU-r15d) family=AU; source="$r15d"; baseline="$plain_r15d"; weights="$r15d/src/nnue_weights.inc" ;;
    AU-kF) family=AU; source="$kf"; baseline="$plain_kf"; weights="$kf/src/nnue_weights.inc" ;;
    T-r15d) family=T; source="$r15d"; baseline="$plain_r15d"; weights="$r15d/src/nnue_weights.inc" ;;
    T-kF) family=T; source="$kf"; baseline="$plain_kf"; weights="$kf/src/nnue_weights.inc" ;;
    C-AU|C-UB) family=AU; source="$root/applied_$tag"; baseline="$plain_r15d"; weights="$r15d/src/nnue_weights.inc" ;;
    C-T) family=T; source="$root/applied_$tag"; baseline="$plain_r15d"; weights="$r15d/src/nnue_weights.inc" ;;
    *) printf 'Unknown Job 22 build label %s\n' "$tag" >&2; exit 2 ;;
  esac
  build="$root/build/$tag"
  receipt="$root/logs/$tag"
  mkdir -p "$root/logs"
  mkdir "$receipt"
  install -m 644 "$baseline/CMakeFiles/forge.dir/flags.make" "$receipt/plain_flags.make.txt"
  inherited=$(sed -n 's/^CMAKE_CXX_FLAGS:STRING=//p' "$baseline/CMakeCache.txt")
  if [[ "$inherited" != *"-march=x86-64-v4"* ]]; then
    printf 'Retained flags lack required architecture selection for %s\n' "$tag" >&2
    exit 2
  fi
  configure=(
    "$cmake" -S "$source" -B "$build" -G "Unix Makefiles"
    -DCMAKE_CXX_COMPILER=/usr/bin/c++ -DCMAKE_BUILD_TYPE=Release
    "-DCMAKE_CXX_FLAGS:STRING=$inherited" "-DCMAKE_CXX_FLAGS_RELEASE:STRING="
    "-DCMAKE_PROJECT_INCLUDE=$root/sanitizer_flags.cmake" "-DJOB22_SANITIZER=$family"
    -DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4 -DFORGE_NNUE_HIDDEN=256
    "-DFORGE_NNUE_WEIGHTS=$weights" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
  )
  compile=("$cmake" --build "$build" --target forge --parallel "${JOB22_JOBS:-2}" --verbose)
  {
    date -u '+%Y-%m-%dT%H:%M:%SZ'
    /usr/bin/c++ --version
    "$cmake" --version
    printf '$ '
    printf '%q ' "${configure[@]}"
    printf '\n$ '
    printf '%q ' "${compile[@]}"
    printf '\n'
  } > "$receipt/commands.txt"
  env -u CXXFLAGS -u CPPFLAGS -u CFLAGS -u LDFLAGS "${configure[@]}" > "$receipt/configure.txt" 2>&1
  python3 -B "$root/verify_flags.py" "$family" "$baseline" "$build" > "$receipt/flag_check.txt"
  install -m 644 "$build/CMakeFiles/forge.dir/flags.make" "$receipt/sanitized_flags.make.txt"
  install -m 644 "$build/CMakeFiles/forge.dir/link.txt" "$receipt/link.txt"
  "${compile[@]}" > "$receipt/build.txt" 2>&1
  {
    date -u '+%Y-%m-%dT%H:%M:%SZ'
    sha256sum "$build/forge"
    printf '%s\n' 'exit_code 0'
  } > "$receipt/outcome.txt"
  printf '%s ready at %s/forge\n' "$tag" "$build"
done
