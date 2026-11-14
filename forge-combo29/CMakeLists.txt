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

# uci.cpp owns main(); the eval test links every other engine translation unit.
set(FORGE_ENGINE_SOURCES ${FORGE_SOURCES})
list(REMOVE_ITEM FORGE_ENGINE_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/src/uci.cpp)
add_executable(test_t14_eval tests_t14/test_eval.cpp ${FORGE_ENGINE_SOURCES})

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

# Same flags on the engine and the test. Node counts depend on this set.
function(forge_apply_lock_flags target)
  target_include_directories(${target} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
  target_compile_definitions(${target} PRIVATE
    NDEBUG
    FORGE_NNUE_HIDDEN=256
    FORGE_EXPOSE_TUNABLES=1
    FORGE_SPD_TT_NOTLS=1
    FORGE_SPD_NO_ZERO_MOVELISTS=2
    FORGE_SEARCH_SPEED2=1
    FORGE_SPD_PREFETCH_EARLY=1)
  if(FORGE_PORTABLE)
    target_compile_definitions(${target} PRIVATE FORGE_SPD_SLIDER_PEXT=0 FORGE_SPD_NNUE_ZMM=0)
  else()
    target_compile_definitions(${target} PRIVATE FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1)
  endif()
  target_compile_options(${target} PRIVATE -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
  target_link_libraries(${target} PRIVATE Threads::Threads)
endfunction()

forge_apply_lock_flags(forge)
forge_apply_lock_flags(test_t14_eval)

enable_testing()
add_test(NAME t14_eval COMMAND test_t14_eval ${CMAKE_CURRENT_SOURCE_DIR}/tests_t14/eval_cases.txt)
