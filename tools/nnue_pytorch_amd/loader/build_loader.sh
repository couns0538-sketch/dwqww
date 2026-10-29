#!/usr/bin/env bash
# R6 J4: build nnue-pytorch's native data loader variants on Windows (BelowNormal, -j2).
# usage: build_loader.sh <variant>   variants: gxx_auto gxx_bmi2_off gxx_pgo clang_msvc clang_msvc_pgo
set -euo pipefail
source /f/opus_scratch/r6/tools/env.sh
SRC=F:/opus_scratch/r6/nnue-pytorch-amd/data_loader/cpp
OUT=F:/opus_scratch/r6/loader
PGO_IN=F:/opus_scratch/r6/nnue-pytorch-amd/.pgo/small.binpack
GXX=C:/msys64/ucrt64/bin/g++.exe
case ${1:-} in gxx*) export PATH="/c/msys64/ucrt64/bin:$PATH" ;; esac
CLANGXX=F:/nnue_pytorch/venv/Lib/site-packages/_rocm_sdk_core/lib/llvm/bin/clang++.exe
LLVM_PROFDATA="C:/Program Files/LLVM/bin/llvm-profdata.exe"
v=$1
b=$OUT/$v
mkdir -p "$b"
cfg() { nice -n 10 cmake -S "$SRC" -B "$1" -G Ninja "${@:2}" > "$1.configure.log" 2>&1; grep -E "BMI2|NNUE_CPU_FAST" "$1.configure.log" || true; }
bld() { nice -n 10 cmake --build "$1" -j 2 "${@:2}" > "$1.build.log" 2>&1 || { tail -30 "$1.build.log"; exit 1; }; }
case $v in
  gxx_auto|gxx_bmi2)
    cfg "$b" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=$GXX "-DCMAKE_SHARED_LINKER_FLAGS=-static -Wl,--exclude-libs,ALL"
    bld "$b" ;;
  gxx_bmi2_off)
    cfg "$b" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=$GXX "-DCMAKE_SHARED_LINKER_FLAGS=-static -Wl,--exclude-libs,ALL" -DNNUE_BMI2=OFF
    bld "$b" ;;
  gxx_pgo|gxx_pgo2)
    cfg "$b.gen" -DCMAKE_BUILD_TYPE=PGO_Generate -DPGO_INPUT=$PGO_IN -DPGO_PROFILE_DATA_DIR=$b/pgo_data -DCMAKE_CXX_COMPILER=$GXX "-DCMAKE_SHARED_LINKER_FLAGS=-static -Wl,--exclude-libs,ALL"
    bld "$b.gen"
    nice -n 10 cmake --build "$b.gen" --target pgo_run > "$b.pgo_run.log" 2>&1 || { tail -20 "$b.pgo_run.log"; exit 1; }
    cfg "$b" -DCMAKE_BUILD_TYPE=PGO_Use -DPGO_PROFILE_DATA_DIR=$b/pgo_data -DCMAKE_CXX_COMPILER=$GXX "-DCMAKE_SHARED_LINKER_FLAGS=-static -Wl,--exclude-libs,ALL"
    bld "$b" ;;
  clang_msvc|clang23_msvc)
    cfg "$b" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_COMPILER=$CLANGXX" -DNNUE_BMI2=ON -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded -DCMAKE_POLICY_DEFAULT_CMP0091=NEW
    bld "$b" ;;
  clang_msvc_pgo)
    cfg "$b.gen" -DCMAKE_BUILD_TYPE=PGO_Generate -DPGO_INPUT=$PGO_IN -DPGO_PROFILE_DATA_DIR=$b/pgo_data "-DCMAKE_CXX_COMPILER=$CLANGXX" -DNNUE_BMI2=ON -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded -DCMAKE_POLICY_DEFAULT_CMP0091=NEW
    bld "$b.gen"
    nice -n 10 cmake --build "$b.gen" --target pgo_run > "$b.pgo_run.log" 2>&1 || { tail -20 "$b.pgo_run.log"; exit 1; }
    "$LLVM_PROFDATA" merge -o "$b/pgo_data/default.profdata" "$b"/pgo_data/*.profraw
    cfg "$b" -DCMAKE_BUILD_TYPE=PGO_Use -DPGO_PROFILE_DATA_DIR=$b/pgo_data/default.profdata "-DCMAKE_CXX_COMPILER=$CLANGXX" -DNNUE_BMI2=ON -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded -DCMAKE_POLICY_DEFAULT_CMP0091=NEW
    bld "$b" ;;
  *) echo "unknown variant $v"; exit 2 ;;
esac
ls -la "$b"/*training_data_loader* | head
