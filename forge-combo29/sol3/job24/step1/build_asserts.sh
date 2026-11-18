#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job24
job=$(realpath forge-combo29/sol3/job24)
base=/workspace/work/sol3-job23/source/A-kF
plain=/workspace/work/sol3-job12/build_F
overlay=$(realpath forge-combo29/sol3/job22/build)
cmake=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
weights=/workspace/work/sol3-job12/tree_F/src/nnue_weights.inc
flags=$(sed -n 's/^CMAKE_CXX_FLAGS:STRING=//p' "$plain/CMakeCache.txt")
[[ "$flags" == *"-march=x86-64-v4"* ]]

for label in "$@"; do
    case "$label" in
        A-kF2|A-wrong2|A-kF2-blind|A-kF-blind) ;;
        *) printf 'Unknown build: %s\n' "$label" >&2; exit 2 ;;
    esac
    source="$root/source/$label"
    build="$root/build/$label"
    logs="$root/build_logs/$label"
    mkdir -p "$root/source" "$root/build" "$root/build_logs"
    mkdir "$source" "$logs"
    cp -a "$base/." "$source/"
    (
        cd "$source"
        if [[ "$label" != A-kF-blind ]]; then
            patch --batch --forward --fuzz=0 -p1 < "$job/step1/A-kF2.patch.txt"
        fi
        if [[ "$label" == A-wrong2 ]]; then
            patch --batch --forward --fuzz=0 -p1 < "$job/step1/A-wrong2.patch.txt"
        fi
        if [[ "$label" == *-blind ]]; then
            patch --batch --forward --fuzz=0 -p1 < "$job/step1/pinned-empty.patch.txt"
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
    compile=("$cmake" --build "$build" --target forge --parallel "${SOL3_JOB24_BUILD_JOBS:-2}" --verbose)
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
