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

# Search experiments. Both default off, so a normal build is the lock tree.
# FORGE_ETC_STATS counts enhanced-transposition opportunities and takes no cutoff.
# FORGE_CONT4_READ adds the ply-4 continuation history (already written) to quiet ordering.
option(FORGE_ETC_STATS "count enhanced transposition opportunities without changing the tree" OFF)
option(FORGE_ETC_HASH_ONLY "with FORGE_ETC_STATS, peek only the hash move" OFF)
option(FORGE_CONT4_READ "order quiets with the ply-4 continuation history the search already writes" OFF)
if(FORGE_ETC_STATS)
  target_compile_definitions(forge PRIVATE FORGE_ETC_STATS=1)
endif()
if(FORGE_ETC_HASH_ONLY)
  target_compile_definitions(forge PRIVATE FORGE_ETC_HASH_ONLY=1)
endif()
if(FORGE_CONT4_READ)
  target_compile_definitions(forge PRIVATE FORGE_CONT4_READ=1)
endif()

# Strict floating-point operation order (required for bit-exact node counts).
target_compile_options(forge PRIVATE -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(forge PRIVATE Threads::Threads)
