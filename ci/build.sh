#!/usr/bin/env bash
# Builds the engine under test for the Fable/Opus checks (Opus, 2026-11-15).
#   bash build.sh <kind> <engine source: the forge-combo29 folder> <build folder>
# kind: release | asan (AddressSanitizer + UBSan, -O1) | tsan (ThreadSanitizer, -O2)
# Always: GCC (g++) with its own C++ library libstdc++ (the reference node counts hold only with it), C++20,
# -DFORGE_NNUE_V3=1, the source untouched (CMake from its CMakeLists.txt; the sanitizer builds lower its -O3 through
# cxx_opt_launcher.sh). If the machine lacks AVX-512 or BMI2, FORGE_PORTABLE=ON with -march=x86-64-v3 (the two
# speed switches it turns off are node-exact by their reports). Also builds the positive control
# (controls/san_control.cpp) with the same compiler and sanitizer flags. Writes <build>.configure.log,
# <build>.build.log and <build>.info.txt next to the build folder.
set -euo pipefail
kind="$1"; src="$2"; out="$3"
here="$(cd "$(dirname "$0")" && pwd)"
info="$out.info.txt"
if grep -qw avx512f /proc/cpuinfo && grep -qw avx512bw /proc/cpuinfo && grep -qw bmi2 /proc/cpuinfo; then
  isa=(-DFORGE_MARCH=x86-64-v4)
  isa_note="x86-64-v4 (AVX-512 and BMI2 present)"
else
  isa=(-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3)
  isa_note="FORGE_PORTABLE=ON, x86-64-v3 (no AVX-512 or no BMI2 on this machine)"
fi
case "$kind" in
  release) san=""; opt="" ;;
  asan)    san="-fsanitize=address,undefined -fno-sanitize-recover=undefined"; opt="-O1" ;;
  tsan)    san="-fsanitize=thread"; opt="-O2" ;;
  *) echo "unknown kind $kind" >&2; exit 2 ;;
esac
args=(-S "$src" -B "$out" -DCMAKE_CXX_COMPILER=g++ "${isa[@]}"
      "-DCMAKE_CXX_FLAGS=-DFORGE_NNUE_V3=1 ${san:+$san -g -fno-omit-frame-pointer}")
if [ -n "$san" ]; then
  args+=("-DCMAKE_EXE_LINKER_FLAGS=$san" "-DCMAKE_CXX_COMPILER_LAUNCHER=$here/cxx_opt_launcher.sh")
  export FORGE_CI_OPT="$opt"
  export FORGE_CI_LAUNCH_LOG="$out.launch.log"
  : > "$FORGE_CI_LAUNCH_LOG"
fi
{
  echo "kind: $kind"
  echo "isa: $isa_note"
  echo "compiler: $(g++ --version | head -n 1)"
  echo "sanitizer flags: ${san:-none}; optimisation: ${opt:-the CMakeLists default -O3}"
  echo "cmake arguments: ${args[*]}"
} > "$info"
cmake "${args[@]}" > "$out.configure.log" 2>&1
cmake --build "$out" -j "$(nproc)" > "$out.build.log" 2>&1
test -x "$out/forge"
if [ -n "$san" ]; then
  # the optimisation flags that really reached the compiler, counted over all its calls (from the launcher)
  sort "$FORGE_CI_LAUNCH_LOG" | uniq -c | sed 's/^/compiler calls with flags: /' >> "$info"
  g++ -std=c++20 "$opt" -g -fno-omit-frame-pointer $san -pthread "$here/controls/san_control.cpp" -o "$out/san_control" \
    >> "$out.build.log" 2>&1
  echo "positive control built: $out/san_control" >> "$info"
fi
echo "built: $out/forge" >> "$info"
