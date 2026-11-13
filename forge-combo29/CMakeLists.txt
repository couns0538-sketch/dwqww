# Forge combo29 lock: plain Linux/CMake build (GCC or Clang).
# This is NOT the Windows lock recipe (clang ThinLTO+PGO, see windows_build/).
# It builds the same source so node counts (bench pins, perft) can be checked.
cmake_minimum_required(VERSION 3.16)
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

# TT audit driver. Same translation units and flags as forge, without uci.cpp (it defines main).
set(FORGE_CORE_SOURCES ${FORGE_SOURCES})
list(FILTER FORGE_CORE_SOURCES EXCLUDE REGEX "/uci\\.cpp$")
add_executable(tt_audit tests/tt_audit.cpp ${FORGE_CORE_SOURCES})
target_include_directories(tt_audit PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_definitions(tt_audit PRIVATE
  NDEBUG
  FORGE_NNUE_HIDDEN=256
  FORGE_EXPOSE_TUNABLES=1
  FORGE_SPD_TT_NOTLS=1
  FORGE_SPD_NO_ZERO_MOVELISTS=2
  FORGE_SEARCH_SPEED2=1
  FORGE_SPD_PREFETCH_EARLY=1
  FORGE_TT_MATE_CLOCK=1
  FORGE_TT_STORE_TERMINAL=1
  FORGE_TT_RESOLVE_SLOT=1)
if(FORGE_PORTABLE)
  target_compile_definitions(tt_audit PRIVATE FORGE_SPD_SLIDER_PEXT=0 FORGE_SPD_NNUE_ZMM=0)
else()
  target_compile_definitions(tt_audit PRIVATE FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1)
endif()
target_compile_options(tt_audit PRIVATE -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
target_link_libraries(tt_audit PRIVATE Threads::Threads)
