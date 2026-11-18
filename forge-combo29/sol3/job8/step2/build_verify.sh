#!/usr/bin/env bash
set -euo pipefail
source_path=$1
build_path=$2
log_path=$3
cmake_cmd=/workspace/work/tools/cmake-python/cmake/data/bin/cmake
flags='-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_NNUE_V3=1 -DFORGE_NNUE_V3_VERIFY=1 -march=x86-64-v4'
quota=4
{
  date -u '+%Y-%m-%dT%H:%M:%SZ Configure started'
  printf ' %q' "$cmake_cmd" -S "$source_path" -B "$build_path" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=$flags"
  printf '\n'
  "$cmake_cmd" --version | sed -n '1p'
  c++ --version | sed -n '1p'
  dpkg-query -W g++-14 libstdc++6 libc6
  cat /sys/fs/cgroup/cpu.max
  "$cmake_cmd" -S "$source_path" -B "$build_path" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=$flags"
  printf ' %q' "$cmake_cmd" --build "$build_path" --parallel "$quota" --verbose
  printf '\n'
  "$cmake_cmd" --build "$build_path" --parallel "$quota" --verbose
  sha256sum "$build_path/forge"
  printf 'uci\nquit\n' | "$build_path/forge" | sed -n '/^id name /p'
  date -u '+%Y-%m-%dT%H:%M:%SZ Build finished'
} > "$log_path" 2>&1
