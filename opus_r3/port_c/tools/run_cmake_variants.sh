#!/usr/bin/env bash
# R3 port C: CMake configurations with FORGE_NNUE_O2 / FORGE_NNUE_INT16 (box flags, static, JOBS=1): the NNUE
# targets and the NNUE + UCI tests (ctest -R 'nnue|net_scale|uci_regression'). usage: run_cmake_variants.sh <name>...
W=/f/opus_scratch/worktrees/opus_r3_port_c
L=/f/opus_scratch/r3/port_c/logs
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
FL="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
TARGETS="forge forge_nnue_v2_tests forge_nnue_v2_uci_tests forge_nnue_threat_tests forge_nnue_pawn_pair_tests forge_pure_nnue_tests forge_nnue_parity_tests forge_nnue_int16_tests forge_nnue_int16_scalar_tests forge_nnue_h512_tests forge_net_scale_tests"
for v in "$@"; do
  case $v in
    o2) X="-DFORGE_NNUE_O2=ON"; T="$TARGETS forge_int16" ;;
    int16) X="-DFORGE_NNUE_INT16=ON"; T="$TARGETS" ;;
    o2_int16) X="-DFORGE_NNUE_O2=ON -DFORGE_NNUE_INT16=ON"; T="$TARGETS" ;;
    *) echo "unknown variant $v"; continue ;;
  esac
  BD=/f/opus_scratch/build/r3_port_c/cmake_$v
  start=$(date +%s)
  nice -n 19 cmake -S "$W" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=C:/msys64/ucrt64/bin/g++.exe \
    "-DCMAKE_CXX_FLAGS=$FL" -DCMAKE_EXE_LINKER_FLAGS=-static -DPython3_EXECUTABLE=C:/Python314/python.exe $X > $L/cmake_$v.configure.log 2>&1 || { echo "$v: configure FAILED"; continue; }
  nice -n 19 cmake --build "$BD" -j 1 --target $T > $L/cmake_$v.build.log 2>&1 || { echo "$v: build FAILED"; tail -30 $L/cmake_$v.build.log; continue; }
  echo "$v: configured [$X], built [$T] in $(( $(date +%s) - start )) s; warnings: $(grep -ci 'warning' $L/cmake_$v.build.log)" > $L/cmake_$v.summary.log
  (cd "$BD" && nice -n 19 ctest -R 'nnue|net_scale|uci_regression' --output-on-failure --timeout 600) > $L/ctest_$v.log 2>&1
  echo "$v: ctest rc $? after $(( $(date +%s) - start )) s" >> $L/cmake_$v.summary.log
  tail -4 $L/ctest_$v.log >> $L/cmake_$v.summary.log
  cat $L/cmake_$v.summary.log
done
echo variants done
