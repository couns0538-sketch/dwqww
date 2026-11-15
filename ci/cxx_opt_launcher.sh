#!/bin/sh
# Compiler launcher for the sanitizer builds of the Fable/Opus checks (Opus, 2026-11-15; the idea is DeepSeek's from
# its trial). The engine's CMakeLists.txt puts -O3 last, which would override the -O1/-O2 a sanitizer build asks for,
# and the source must not be changed. CMake calls this script as  <launcher> <compiler> <arguments...>  (through
# CMAKE_CXX_COMPILER_LAUNCHER); every argument "-O3" is replaced by the level in FORGE_CI_OPT (for example -O1), and
# everything else is passed on unchanged.
set -eu
compiler="$1"
shift
level="${FORGE_CI_OPT:--O3}"
for a in "$@"; do
    shift
    if [ "$a" = "-O3" ]; then
        set -- "$@" "$level"
    else
        set -- "$@" "$a"
    fi
done
# Evidence: the optimisation flags each real compiler call got, one line per call (FORGE_CI_LAUNCH_LOG, if set)
if [ -n "${FORGE_CI_LAUNCH_LOG:-}" ]; then
    flags=""
    for a in "$@"; do
        case "$a" in -O*) flags="$flags $a" ;; esac
    done
    echo "call:$flags" >> "$FORGE_CI_LAUNCH_LOG"
fi
exec "$compiler" "$@"
