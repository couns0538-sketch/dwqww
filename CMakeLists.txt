cmake_minimum_required(VERSION 3.16)
project(ChessEngineForge VERSION 6.1.0 LANGUAGES CXX)
find_package(Threads REQUIRED)

option(FORGE_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(FORGE_NATIVE "Optimise for the build machine's CPU (-march=native)" OFF)
# Without a hardware popcount the compiler emits a libgcc call for every
# std::popcount, which costs the bitboard evaluation about 10% of its speed.
# POPCNT has been available on every x86-64 CPU since 2008; set this ON only
# for binaries that must run on older hardware.
option(FORGE_PORTABLE "Build for the baseline x86-64 ISA without POPCNT" OFF)

add_library(forge_core
    src/bitboard.cpp
    src/board.cpp
    src/eval.cpp
    src/eval_params.cpp
    src/search.cpp
)
target_include_directories(forge_core PUBLIC include)
target_compile_features(forge_core PUBLIC cxx_std_20)

if(MSVC)
    target_compile_options(forge_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(forge_core PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
    if(FORGE_NATIVE)
        target_compile_options(forge_core PUBLIC -march=native)
    elseif(NOT FORGE_PORTABLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "(x86_64|AMD64|amd64)")
        target_compile_options(forge_core PUBLIC -mpopcnt)
    endif()
    if(FORGE_ENABLE_SANITIZERS)
        target_compile_options(forge_core PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(forge_core PUBLIC -fsanitize=address,undefined)
    endif()
endif()

add_executable(forge src/uci.cpp)
target_link_libraries(forge PRIVATE forge_core Threads::Threads)

add_executable(forge_tests tests/tests.cpp)
target_link_libraries(forge_tests PRIVATE forge_core Threads::Threads)

add_executable(forge_bench bench/benchmark.cpp)
target_link_libraries(forge_bench PRIVATE forge_core Threads::Threads)

enable_testing()
add_test(NAME forge_tests COMMAND forge_tests)

# Support tooling does not change engine behavior or add runtime dependencies.
option(FORGE_BUILD_VALIDATION_TOOLS "Build the original opening corpus generator" OFF)
if(FORGE_BUILD_VALIDATION_TOOLS)
    add_executable(forge_openings tools/generate_openings.cpp)
    target_link_libraries(forge_openings PRIVATE forge_core)
endif()
option(FORGE_BUILD_TUNING_TOOLS "Build the evaluation tuning tools (position extractor and Texel tuner)" OFF)
if(FORGE_BUILD_TUNING_TOOLS)
    add_executable(forge_extract tools/tune/extract.cpp)
    target_link_libraries(forge_extract PRIVATE forge_core)
    add_executable(forge_texel tools/tune/texel.cpp)
    target_link_libraries(forge_texel PRIVATE forge_core Threads::Threads)
endif()
find_package(Python3 3.10 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND)
    add_test(NAME match_tool_tests
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/match/test_match_tools.py)
    add_test(NAME uci_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/uci_regression.py
                $<TARGET_FILE:forge> --log ${CMAKE_CURRENT_BINARY_DIR}/uci-regression.log)
    add_test(NAME ponder_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/ponder_regression.py
                $<TARGET_FILE:forge>)
endif()
