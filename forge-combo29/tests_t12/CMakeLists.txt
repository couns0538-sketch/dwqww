cmake_minimum_required(VERSION 3.16)
project(forge_t12_tests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

set(FORGE_MARCH "x86-64-v3" CACHE STRING "value for -march")
option(FORGE_PORTABLE "build without PEXT/AVX-512 speed switches" ON)
option(FORGE_SANITIZE "build with AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

set(FORGE_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/..)

set(FORGE_ENGINE_SOURCES
  ${FORGE_ROOT}/src/bitboard.cpp
  ${FORGE_ROOT}/src/board.cpp
  ${FORGE_ROOT}/src/book.cpp
  ${FORGE_ROOT}/src/eval.cpp
  ${FORGE_ROOT}/src/eval_params.cpp
  ${FORGE_ROOT}/src/nnue.cpp
  ${FORGE_ROOT}/src/search.cpp
)

add_executable(krk_mate_test
  krk_mate_test.cpp
  ${FORGE_ENGINE_SOURCES}
)

target_include_directories(krk_mate_test PRIVATE ${FORGE_ROOT}/include)

target_compile_definitions(krk_mate_test PRIVATE
  FORGE_NNUE_HIDDEN=256
  FORGE_EXPOSE_TUNABLES=1
  FORGE_SPD_TT_NOTLS=1
  FORGE_SPD_NO_ZERO_MOVELISTS=2
  FORGE_SEARCH_SPEED2=1
  FORGE_SPD_PREFETCH_EARLY=1
)

if(NOT FORGE_SANITIZE)
  target_compile_definitions(krk_mate_test PRIVATE NDEBUG)
endif()

if(FORGE_PORTABLE)
  target_compile_definitions(krk_mate_test PRIVATE FORGE_SPD_SLIDER_PEXT=0 FORGE_SPD_NNUE_ZMM=0)
else()
  target_compile_definitions(krk_mate_test PRIVATE FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1)
endif()

if(FORGE_SANITIZE)
  target_compile_options(krk_mate_test PRIVATE
    -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined
    -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
  target_link_options(krk_mate_test PRIVATE -fsanitize=address,undefined)
else()
  target_compile_options(krk_mate_test PRIVATE
    -O3 -ffp-contract=off -fno-fast-math -march=${FORGE_MARCH})
endif()

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(krk_mate_test PRIVATE Threads::Threads)
