# Forge combo29 lock: plain Linux/CMake build (GCC or Clang).
# This is NOT the Windows lock recipe (clang ThinLTO+PGO, see windows_build/).
# It builds the same source so node counts (bench pins, perft) can be checked.
cmake_minimum_required(VERSION 3.16)
# Clang's compiler check links a program before any target exists. On Debian and
# Ubuntu the unversioned libstdc++.so is in GCC's private directory, which Clang
# does not search. Add that directory before project() so the check can link.
if(CMAKE_CXX_COMPILER MATCHES "[Cc]lang")
  execute_process(COMMAND g++ -dumpversion OUTPUT_VARIABLE FORGE_GCC_VER OUTPUT_STRIP_TRAILING_WHITESPACE)
  execute_process(COMMAND g++ -dumpmachine OUTPUT_VARIABLE FORGE_GCC_TRIPLE OUTPUT_STRIP_TRAILING_WHITESPACE)
  execute_process(
    COMMAND g++ -print-file-name=libstdc++.so
    OUTPUT_VARIABLE FORGE_LIBSTDCXX
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE FORGE_LIBSTDCXX_RC)
  set(FORGE_LIBSTDCXX_DIR "")
  if(FORGE_LIBSTDCXX_RC EQUAL 0 AND EXISTS "${FORGE_LIBSTDCXX}")
    get_filename_component(FORGE_LIBSTDCXX_DIR "${FORGE_LIBSTDCXX}" DIRECTORY)
    string(APPEND CMAKE_EXE_LINKER_FLAGS " -L${FORGE_LIBSTDCXX_DIR}")
    string(APPEND CMAKE_SHARED_LINKER_FLAGS " -L${FORGE_LIBSTDCXX_DIR}")
  endif()
  # This image's Clang looks for GCC 14 headers while only GCC 13 is installed.
  # A Clang that already finds <array> is left alone. The version and triple come
  # from g++, not from a hardcoded compiler release.
  file(WRITE /tmp/forge_cxx_probe.cpp "#include <array>\nint main(){return 0;}\n")
  if(FORGE_LIBSTDCXX_DIR STREQUAL "")
    execute_process(
      COMMAND ${CMAKE_CXX_COMPILER} /tmp/forge_cxx_probe.cpp -o /tmp/forge_cxx_probe
      RESULT_VARIABLE FORGE_CXX_PROBE_RC
      OUTPUT_QUIET ERROR_QUIET)
  else()
    execute_process(
      COMMAND ${CMAKE_CXX_COMPILER} /tmp/forge_cxx_probe.cpp -o /tmp/forge_cxx_probe -L${FORGE_LIBSTDCXX_DIR}
      RESULT_VARIABLE FORGE_CXX_PROBE_RC
      OUTPUT_QUIET ERROR_QUIET)
  endif()
  if(NOT FORGE_CXX_PROBE_RC EQUAL 0)
    set(FORGE_CXX_INC "/usr/include/c++/${FORGE_GCC_VER}")
    set(FORGE_CXX_INC_ARCH "/usr/include/${FORGE_GCC_TRIPLE}/c++/${FORGE_GCC_VER}")
    if(EXISTS "${FORGE_CXX_INC}/array" AND EXISTS "${FORGE_CXX_INC_ARCH}/bits/c++config.h")
      string(APPEND CMAKE_CXX_FLAGS " -I${FORGE_CXX_INC} -I${FORGE_CXX_INC_ARCH}")
    endif()
  endif()
endif()
project(forge_combo29 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

# FORGE_MARCH: target CPU. The lock needs BMI2 (PEXT sliders) and AVX-512F (NNUE ZMM kernel).
set(FORGE_MARCH "x86-64-v4" CACHE STRING "value for -march (lock exe uses znver5)")
# FORGE_PORTABLE=ON drops the two ISA-bound speed switches (SLIDER_PEXT, NNUE_ZMM) so it
# builds on CPUs without AVX-512/BMI2. Use -DFORGE_MARCH=x86-64-v3 or native with it.
option(FORGE_PORTABLE "build without the PEXT/AVX-512 speed switches" OFF)

file(GLOB FORGE_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
add_executable(forge ${FORGE_SOURCES})
target_include_directories(forge PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

target_compile_definitions(forge PRIVATE
  NDEBUG
  FORGE_NNUE_HIDDEN=256
  FORGE_EXPOSE_TUNABLES=1
  FORGE_SPD_TT_NOTLS=1
  FORGE_SPD_NO_ZERO_MOVELISTS=2
  FORGE_SEARCH_SPEED2=1
  FORGE_SPD_PREFETCH_EARLY=1)
if(FORGE_PORTABLE)
  target_compile_definitions(forge PRIVATE FORGE_SPD_SLIDER_PEXT=0 FORGE_SPD_NNUE_ZMM=0)
else()
  target_compile_definitions(forge PRIVATE FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1)
endif()

# Strict floating-point operation order (required for bit-exact node counts).
target_compile_options(forge PRIVATE -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(forge PRIVATE Threads::Threads)

# Clang does not search GCC's private library directory, so -lstdc++ fails on
# Debian/Ubuntu layouts where only libstdc++.so.6 is on the default linker path.
# Ask g++ where its libstdc++.so lives and add that directory.
function(forge_link_stdcxx target_name)
  if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    execute_process(
      COMMAND g++ -print-file-name=libstdc++.so
      OUTPUT_VARIABLE forge_libstdcxx
      OUTPUT_STRIP_TRAILING_WHITESPACE
      RESULT_VARIABLE forge_libstdcxx_rc)
    if(forge_libstdcxx_rc EQUAL 0 AND EXISTS "${forge_libstdcxx}")
      get_filename_component(forge_libstdcxx_dir "${forge_libstdcxx}" DIRECTORY)
      target_link_directories(${target_name} PRIVATE "${forge_libstdcxx_dir}")
    endif()
  endif()
endfunction()
forge_link_stdcxx(forge)

set(FORGE_LIB_SOURCES ${FORGE_SOURCES})
list(FILTER FORGE_LIB_SOURCES EXCLUDE REGEX "/uci\\.cpp$")

# In-process checks (perft, NNUE incremental, mirror eval, mate/draw). Same
# compile flags as the engine so the results match the release binary.
add_executable(forge_checks ${FORGE_LIB_SOURCES} ${CMAKE_CURRENT_SOURCE_DIR}/tests/engine_checks.cpp)
target_include_directories(forge_checks PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_definitions(forge_checks PRIVATE
  NDEBUG
  FORGE_NNUE_HIDDEN=256
  FORGE_EXPOSE_TUNABLES=1
  FORGE_SPD_TT_NOTLS=1
  FORGE_SPD_NO_ZERO_MOVELISTS=2
  FORGE_SEARCH_SPEED2=1
  FORGE_SPD_PREFETCH_EARLY=1)
if(FORGE_PORTABLE)
  target_compile_definitions(forge_checks PRIVATE FORGE_SPD_SLIDER_PEXT=0 FORGE_SPD_NNUE_ZMM=0)
else()
  target_compile_definitions(forge_checks PRIVATE FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1)
endif()
target_compile_options(forge_checks PRIVATE -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
target_link_libraries(forge_checks PRIVATE Threads::Threads)
forge_link_stdcxx(forge_checks)

# v3 file-format and incremental-accumulator tests. Not part of the default engine.
add_executable(forge_nnue_v3_tests ${FORGE_LIB_SOURCES}
  ${CMAKE_CURRENT_SOURCE_DIR}/../h512/tools/nnue_v3_tests.cpp)
target_include_directories(forge_nnue_v3_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_definitions(forge_nnue_v3_tests PRIVATE
  NDEBUG
  FORGE_NNUE_HIDDEN=256
  FORGE_NNUE_V3=1
  FORGE_EXPOSE_TUNABLES=1
  FORGE_SPD_TT_NOTLS=1
  FORGE_SPD_NO_ZERO_MOVELISTS=2
  FORGE_SEARCH_SPEED2=1
  FORGE_SPD_PREFETCH_EARLY=1)
if(FORGE_PORTABLE)
  target_compile_definitions(forge_nnue_v3_tests PRIVATE FORGE_SPD_SLIDER_PEXT=0 FORGE_SPD_NNUE_ZMM=0)
else()
  target_compile_definitions(forge_nnue_v3_tests PRIVATE FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1)
endif()
target_compile_options(forge_nnue_v3_tests PRIVATE -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
target_link_libraries(forge_nnue_v3_tests PRIVATE Threads::Threads)
forge_link_stdcxx(forge_nnue_v3_tests)
